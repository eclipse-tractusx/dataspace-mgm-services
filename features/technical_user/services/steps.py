#################################################################################
#  Copyright (c) 2026 Contributors to the Eclipse Foundation
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  This program and the accompanying materials are made available under the
#  terms of the Apache License, Version 2.0 which is available at
#  https://www.apache.org/licenses/LICENSE-2.0.
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: GitHub Copilot (Claude Sonnet 5.5)
#################################################################################
"""Steps for Process Orchestration (README 8); every step is idempotent through its business key (6.9)."""
from __future__ import annotations

from collections.abc import Callable

from portal_common.models import StepResult

from ..managers import config
from ..managers import neighbour_client as gateways
from ..managers.technical_user_repository import repository
from ..models import (
    LIVE_STATUSES,
    Origin,
    Status,
    SubscriptionParty,
    TechnicalUserRecord,
    validation,
)
from ..models.responses import (
    CompanyTechnicalUsers,
    SubscriptionAccount,
    SubscriptionAccounts,
    SubscriptionTechnicalUsers,
    WalletResult,
)
from ..models.schemas import (
    StepApplyWalletAccess,
    StepCompanyRef,
    StepCreateForSubscription,
    StepSubscriptionRef,
    StepTechnicalUserRef,
    role_refs,
)
from . import accounts, audit, iam_access, roles, state
from .audit import Actor


def _subscription_account(data: StepCreateForSubscription, *, party: SubscriptionParty, company_id: str,
                          role_names: list[str], co_viewer_company_id: str | None,
                          actor: Actor) -> SubscriptionAccount:
    subscription_id = data.offer_subscription_id
    row = repository.find_subscription(subscription_id, party)
    if row is None:
        client_id = accounts.draw_client_id()
        row = accounts.new_row(company_id=company_id, name=f"{client_id}-{data.name}", description=None,
                               origin=Origin.SUBSCRIPTION, client_id=client_id,
                               offer_subscription_id=subscription_id, subscription_party=party,
                               co_viewer_company_id=co_viewer_company_id)
    wallet_requested = party == SubscriptionParty.CUSTOMER and bool(set(role_names) & config.wallet_roles())
    _, assigned = roles.split(role_names)
    iam = iam_access.iam()
    first_completion = row["iam_client_uuid"] is None
    before = set() if first_completion else set(iam_access.call(iam.roles_for, row["iam_client_id"]))
    company = gateways.company(company_id)
    created = iam_access.call(iam.create_or_complete, row["iam_client_id"], owner_id=row["id"], name=row["name"],
                              description=None, company_id=company_id, bpn=company["bpn"], roles=assigned,
                              enabled=not row["disabled"] and row["status"] != Status.INACTIVE)
    if first_completion:
        after = set(iam_access.call(iam.roles_for, row["iam_client_id"]))
        accounts.complete_creation(row, created, wallet_requested=wallet_requested,
                                   added_roles=sorted(after - before), operation="create-for-subscription",
                                   actor=actor)
    else:
        restored = sorted(set(iam_access.call(iam.roles_for, row["iam_client_id"])) - before)
        if restored:   # roles that were missing in the Portal IAM and were assigned again by this retry
            with repository.transaction():
                accounts.touch(row)
                audit.record(row, "create-for-subscription", actor)
                audit.record_role_changes(row, restored, [], "create-for-subscription", actor)
    return SubscriptionAccount(technical_user_id=row["id"], subscription_party=party,
                               iam_client_id=row["iam_client_id"], status=row["status"],
                               wallet_access=row["wallet_access"], roles=role_refs(role_names))


def create_for_subscription(input: dict) -> StepResult[SubscriptionAccounts]:
    data = validation.parse(StepCreateForSubscription, input)
    role_names = data.role_names
    roles.check_exist(role_names)
    provider_only = set(role_names) & config.provider_roles()
    customer_roles = [name for name in role_names if name not in config.provider_roles()]
    actor = Actor.process(data)
    # lock order company, subscription, account: a deactivation of a company or the subscription cannot run
    # between the check of the company and the creation of its account
    keys = [f"company:{data.customer_company_id}", f"subscription:{data.offer_subscription_id}"]
    if provider_only:
        keys.append(f"company:{data.provider_company_id}")
    with repository.locked_all(*keys):
        gateways.company_ready(data.customer_company_id)
        if provider_only:
            gateways.company_ready(data.provider_company_id)
        result = [_subscription_account(data, party=SubscriptionParty.CUSTOMER, company_id=data.customer_company_id,
                                        role_names=customer_roles, co_viewer_company_id=data.provider_company_id,
                                        actor=actor)]
        if provider_only:
            result.append(_subscription_account(data, party=SubscriptionParty.PROVIDER,
                                                company_id=data.provider_company_id,
                                                role_names=sorted(provider_only), co_viewer_company_id=None,
                                                actor=actor))
    reply = SubscriptionAccounts(offer_subscription_id=data.offer_subscription_id, accounts=result)
    return StepResult[SubscriptionAccounts].done(data, reply)


def _wallet_result(row: TechnicalUserRecord) -> WalletResult:
    return WalletResult(technical_user_id=row["id"], status=row["status"], wallet_access=row["wallet_access"],
                        wallet_account_ref=row["wallet_account_ref"])


def apply_wallet_access(input: dict) -> StepResult[WalletResult]:
    data = validation.parse(StepApplyWalletAccess, input)
    with repository.locked(f"technical-user:{data.technical_user_id}"):
        row = accounts.find(data.technical_user_id)
        if state.apply_wallet_outcome(row, data.outcome, data.wallet_account_ref):
            with repository.transaction():
                accounts.touch(row)
                audit.record(row, "apply-wallet-access", Actor.process(data))
        return StepResult[WalletResult].done(data, _wallet_result(row))


def delete(input: dict) -> StepResult[WalletResult]:
    data = validation.parse(StepTechnicalUserRef, input)
    with repository.locked(f"technical-user:{data.technical_user_id}"):
        row = accounts.find(data.technical_user_id)
        if row["status"] != Status.DELETED:
            state.require_removal_pending(row)
            accounts.delete_account(row, operation="delete", actor=Actor.process(data))
        return StepResult[WalletResult].done(data, _wallet_result(row))


def _set_client_enabled(row: TechnicalUserRecord, enabled: bool) -> None:
    if row["iam_client_uuid"]:
        iam_access.call(iam_access.iam().set_enabled, row["iam_client_id"], enabled)


def _save_with_audit(row: TechnicalUserRecord, operation: str, actor: Actor) -> None:
    with repository.transaction():
        accounts.touch(row)
        audit.record(row, operation, actor)


def _each_locked(candidates: list[TechnicalUserRecord], applies: Callable[[TechnicalUserRecord], bool],
                 work: Callable[[TechnicalUserRecord], None]) -> None:
    """Runs `work` on each account under the lock of that account, on the row as it is by then (a wallet result or a
    change may have been stored since the list was read) and only if `applies` still holds."""
    for candidate in candidates:
        with repository.locked(f"technical-user:{candidate['id']}"):
            row = repository.get(candidate["id"])
            if row is not None and applies(row):
                work(row)


def _disable(row: TechnicalUserRecord, operation: str, actor: Actor) -> None:
    _set_client_enabled(row, False)
    state.disable(row)
    _save_with_audit(row, operation, actor)


def _enable(row: TechnicalUserRecord, operation: str, actor: Actor) -> None:
    if state.client_enabled_after_enable(row):
        _set_client_enabled(row, True)
    state.enable(row)
    _save_with_audit(row, operation, actor)


def _deactivate(row: TechnicalUserRecord, actor: Actor) -> None:
    _set_client_enabled(row, False)
    state.deactivate_subscription_account(row)
    _save_with_audit(row, "disable-subscription-technical-users", actor)


def _switch_company(input: dict, *, disable: bool) -> StepResult[CompanyTechnicalUsers]:
    """8.4 and 8.5: every live account of the company to `disabled == disable`; the reply lists all of them."""
    data = validation.parse(StepCompanyRef, input)
    company_id, actor = data.company_id, Actor.process(data)
    operation = "disable-company-technical-users" if disable else "enable-company-technical-users"
    with repository.locked(f"company:{company_id}"):
        _each_locked(repository.find(owner_company_id=company_id, statuses=LIVE_STATUSES, disabled=not disable),
                     lambda row: row["disabled"] != disable and row["status"] in LIVE_STATUSES,
                     lambda row: (_disable if disable else _enable)(row, operation, actor))
        ids = [row["id"] for row in repository.find(owner_company_id=company_id, statuses=LIVE_STATUSES,
                                                    disabled=disable)]
    reply = CompanyTechnicalUsers(company_id=company_id, technical_user_ids=sorted(ids))
    return StepResult[CompanyTechnicalUsers].done(data, reply)


def disable_company_technical_users(input: dict) -> StepResult[CompanyTechnicalUsers]:
    return _switch_company(input, disable=True)


def enable_company_technical_users(input: dict) -> StepResult[CompanyTechnicalUsers]:
    return _switch_company(input, disable=False)


def disable_subscription_technical_users(input: dict) -> StepResult[SubscriptionTechnicalUsers]:
    data = validation.parse(StepSubscriptionRef, input)
    subscription_id, actor = data.offer_subscription_id, Actor.process(data)
    with repository.locked(f"subscription:{subscription_id}"):
        _each_locked(repository.find(offer_subscription_id=subscription_id, statuses=(Status.PENDING, Status.ACTIVE)),
                     lambda row: row["status"] in (Status.PENDING, Status.ACTIVE),
                     lambda row: _deactivate(row, actor))
        ids = [row["id"] for row in repository.find(offer_subscription_id=subscription_id,
                                                    statuses=(Status.INACTIVE,))]
    reply = SubscriptionTechnicalUsers(offer_subscription_id=subscription_id, technical_user_ids=sorted(ids))
    return StepResult[SubscriptionTechnicalUsers].done(data, reply)

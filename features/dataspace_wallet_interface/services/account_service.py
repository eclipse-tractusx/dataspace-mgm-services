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
#  Assisted-By: Claude Code (claude-sonnet-5-5)
#################################################################################
"""Wallet accounts of C4-M2 (README 5, 6.3, 6.7, 6.10, 7.2, 7.3, 7.6, 8.2, 8.3, 9.2, 10).

A wallet account is the access of a technical user to the dataspace wallet of its company. The steps
`create-wallet-account` and `delete-wallet-account` are long-running: they answer `RUNNING` when the account was not
complete at the time of the call and the end is reported by an event (README 6.9). Steps and callbacks of one
technical user never run at the same time (a lock per technical user, README 6.9). Time is read only through
`service.now()` at call time. The wallet, the company, the clock, the audit log and the encryption belong to the
core (`wallet_service.py`, `managers/crypto.py`); the providers are asked through `providers.get(...)`. The HTTP
operations are in `controllers/` (steps, `technical_users/`, `internal/`, `callbacks/`).
"""
from __future__ import annotations

import contextlib
import datetime as dt
import uuid
from typing import Final

from portal_common import events

from ..managers import config, crypto, providers
from ..models import MODULE
from ..models.api import WalletAccount, WalletAccountCredentials, WalletAccountStepReply, WalletAccountStepResult
from ..models.errors import problem as _problem
from ..models.value_sets import StepState
from . import wallet_service as service

REQUESTED: Final = "REQUESTED"
ACTIVE: Final = "ACTIVE"
FAILED: Final = "FAILED"
DELETING: Final = "DELETING"
DELETED: Final = "DELETED"
NONE, AVAILABLE, RETRIEVED, EXPIRED = "NONE", "AVAILABLE", "RETRIEVED", "EXPIRED"


# --------------------------------------------------------------------------------------- helpers
def _lock(technical_user_id: str) -> contextlib.AbstractContextManager:
    """README 6.9: one writer per technical user (the in-memory stand-in of the advisory lock)."""
    return service.get_store().transaction(f"technical-user:{technical_user_id}")


def _uuid(value: object, name: str) -> str:
    try:
        if not isinstance(value, str):
            raise ValueError
        uuid.UUID(value)
    except ValueError:
        raise _problem(400, "validation", f"{name} must be a UUID") from None
    return value


def _validate(input: dict) -> tuple[str, str]:
    """README 8.2, 8.3 input: `processId`, `stepRunId`, `technicalUserId`, `companyId`; returns the last two."""
    if not isinstance(input, dict):
        raise _problem(400, "validation", "the input must be a JSON object")
    for name in ("processId", "stepRunId"):
        _uuid(input.get(name), name)
    return _uuid(input.get("technicalUserId"), "technicalUserId"), _uuid(input.get("companyId"), "companyId")


def _save(account: dict) -> dict:
    account["changed_at"] = service.now()
    service.get_store().put_account(account)
    return account


def _result(account: dict) -> WalletAccountStepResult:
    """README 8.2 and 8.3 result (openapi `StepResultWalletAccount`); no secrets."""
    reason = {"failure_reason": account["failure_reason"]} if account.get("failure_reason") else {}
    return WalletAccountStepResult(wallet_account_ref=account["id"], technical_user_id=account["technical_user_id"],
                                   company_id=account["company_id"], provider=account["provider"],
                                   status=account["status"], **reason)


def _reply(input: dict, step: str, state: StepState, account: dict) -> WalletAccountStepReply:
    service.log_step(input, step, account["id"], state)
    return WalletAccountStepReply(step_run_id=input["stepRunId"], state=state, result=_result(account))


# ------------------------------------------------------------------------------------------ views
def _view(account: dict) -> WalletAccount:
    """README 7.2 and 9.2 body (openapi `WalletAccount`): the state of the credentials, never the credentials."""
    expires = None
    if account.get("credentials_state") == AVAILABLE:
        row = service.get_store().get_account_credentials(account["id"])
        expires = service.iso(row["expires_at"]) if row else None
    return WalletAccount(wallet_account_ref=account["id"], technical_user_id=account["technical_user_id"],
                         company_id=account["company_id"], provider=account["provider"], status=account["status"],
                         failure_reason=account.get("failure_reason"), credentials_state=account["credentials_state"],
                         credentials_expire_at=expires, created_at=service.iso(account.get("created_at")),
                         changed_at=service.iso(account.get("changed_at")))


def _current(technical_user_id: str) -> dict:
    """README 7.2 step 2: the row with a status other than `DELETED`, otherwise the latest; none is 404."""
    account = service.get_store().get_account(technical_user_id)
    if account is None:
        raise _problem(404, "not-found", "no wallet account for this technical user")
    return account


def get_wallet_account_internal(*, technicalUserId: str) -> WalletAccount:
    """Query `getWalletAccountInternal` (README 9.2): as 7.2, without the check of the company."""
    return _view(_current(technicalUserId))


def view_wallet_account(technical_user_id: str, claims: dict) -> WalletAccount:
    """`GET /technical-users/{id}/wallet-account` (README 7.2): another company's account stays invisible (404)."""
    account = _current(technical_user_id)
    if not claims.get("company_id") or claims["company_id"] != account["company_id"]:
        raise _problem(404, "not-found", "no wallet account for this technical user")
    return _view(account)


# ---------------------------------------------------------------------------- transitions (README 6.3)
def _publish(type_: str, account: dict, **extra: object) -> None:
    events.publish(MODULE, type_, {"technicalUserId": account["technical_user_id"], "companyId": account["company_id"],
                                   "walletAccountRef": account["id"], **extra})


def _activate(account: dict, token_url: str, client_id: str, secret: str) -> dict:
    """`REQUESTED` to `ACTIVE`: keep the credentials encrypted until they are retrieved (README 6.7)."""
    moment = service.now()
    ciphertext, nonce, key_version = crypto.encrypt(secret)
    service.get_store().put_account_credentials(
        account["id"], token_url, client_id, ciphertext, nonce, key_version, moment,
        moment + dt.timedelta(days=config.account_credentials_retention_days()))
    account.update(status=ACTIVE, credentials_state=AVAILABLE, failure_reason=None,
                   provider_ordered_at=account.get("provider_ordered_at") or moment)
    _save(account)
    _publish("WalletAccountCreated", account, provider=account["provider"])
    return account


def _fail(account: dict, reason: str) -> dict:
    account.update(status=FAILED, failure_reason=reason)
    _save(account)
    _publish("WalletAccountFailed", account, reason=reason)
    return account


def _delete(account: dict) -> dict:
    """To `DELETED`: the row of the credentials goes with it (README 6.3)."""
    service.get_store().delete_account_credentials(account["id"])
    account["status"] = DELETED
    _save(account)
    _publish("WalletAccountDeleted", account)
    return account


# ------------------------------------------------------------------------- create-wallet-account
def _check_preconditions(company_id: str) -> dict:
    """README 8.2 preconditions: the wallet is `ACTIVE` (read in the own table), the company is `ACTIVE` at C3-M1."""
    wallet = service.get_wallet(company_id)
    if wallet is None or wallet["status"] != "ACTIVE":
        raise _problem(409, "wallet-not-active", "the wallet of the company is not ACTIVE")
    company = service.get_company(company_id)
    if company is None:
        raise _problem(404, "not-found", "company not found")
    if company.get("status") != "ACTIVE":
        raise _problem(409, "company-not-active", "no new wallet account for a company that is not ACTIVE")
    return wallet


def _new_account(technical_user_id: str, company_id: str, wallet: dict) -> dict:
    moment = service.now()
    return {"id": str(uuid.uuid4()), "technical_user_id": technical_user_id, "company_id": company_id,
            "wallet_id": wallet["id"], "provider": wallet["provider"], "status": REQUESTED, "failure_reason": None,
            "provider_name": f"tu-{technical_user_id}", "provider_ordered_at": None, "deletion_ordered_at": None,
            "credentials_state": NONE, "created_at": moment, "changed_at": moment}


def _order(account: dict, wallet: dict) -> dict:
    """README 8.2 step 4. `provider_ordered_at` is set only after the provider accepted the order."""
    adapter = providers.get(account["provider"])
    order = {"company_id": account["company_id"], "bpn": wallet["bpn"],
             "technical_user_id": account["technical_user_id"], "wallet_account_ref": account["id"],
             "provider_name": account["provider_name"]}
    if adapter.provider == "IDENTITY_HUB":
        order["sts_access"] = service.wallet_secret(wallet["id"], service.STS_ACCESS)
    answer = adapter.order_account(order)
    # An in-process stand-in may already have called back while ordering: continue from the stored row.
    account = service.get_store().get_account_by_ref(account["id"]) or account
    if answer["result"] == "CREATED":
        return _activate(account, answer["token_url"], answer["client_id"], answer["client_secret"])
    if answer["result"] == "NOT_SUPPORTED":
        return _fail(account, "NOT_SUPPORTED_BY_PROVIDER")
    account["provider_ordered_at"] = account.get("provider_ordered_at") or service.now()
    return _save(account)


def create_wallet_account(input: dict) -> WalletAccountStepReply:
    """Step `create-wallet-account` (README 8.2)."""
    technical_user_id, company_id = _validate(input)
    with _lock(technical_user_id):
        account = service.get_store().get_account(technical_user_id)
        if account is not None and account["status"] == DELETED:
            account = None
        state: StepState = "RUNNING"
        if account is not None:
            if account["company_id"] != company_id:
                raise _problem(409, "conflict", "the technical user has a wallet account of another company")
            if account["status"] in (ACTIVE, FAILED):
                return _reply(input, "create-wallet-account", "DONE", account)
            if account["status"] == DELETING:
                raise _problem(409, "invalid-state", "the wallet account is being deleted")
            if account.get("provider_ordered_at"):
                return _reply(input, "create-wallet-account", state, account)
        wallet = _check_preconditions(company_id)
        if account is None:
            account = _save(_new_account(technical_user_id, company_id, wallet))
        account = _order(account, wallet)
        return _reply(input, "create-wallet-account", state, account)


# ------------------------------------------------------------------------- delete-wallet-account
def _order_deletion(account: dict) -> dict:
    """README 8.3 step 4 for SAP DIV: the order goes out; `deletion_ordered_at` only after it was accepted."""
    wallet = service.get_wallet(account["company_id"])
    answer = providers.get(account["provider"]).order_account_deletion({
        "bpn": wallet["bpn"] if wallet else "", "technical_user_id": account["technical_user_id"],
        "wallet_account_ref": account["id"], "provider_name": account["provider_name"]})
    account = service.get_store().get_account_by_ref(account["id"]) or account
    if answer["result"] == "DELETED":
        return _delete(account)
    account["deletion_ordered_at"] = account.get("deletion_ordered_at") or service.now()
    return _save(account)


def delete_wallet_account(input: dict) -> WalletAccountStepReply:
    """Step `delete-wallet-account` (README 8.3). The status of the company does not matter."""
    technical_user_id, company_id = _validate(input)
    reference = input.get("walletAccountRef")
    if reference is not None:
        _uuid(reference, "walletAccountRef")
    with _lock(technical_user_id):
        account = service.get_store().get_account(technical_user_id)
        if account is not None and account["status"] == REQUESTED:
            raise _problem(409, "invalid-state", "the wallet account is not complete yet")
        if reference is not None and account is not None and account["id"] != reference:
            raise _problem(409, "conflict", "walletAccountRef is not the current wallet account of the technical user")
        if account is None:
            service.log_step(input, "delete-wallet-account", technical_user_id, "DONE")
            return WalletAccountStepReply(step_run_id=input["stepRunId"], state="DONE", result=WalletAccountStepResult(
                technical_user_id=technical_user_id, company_id=company_id, status=DELETED))
        if account["status"] == DELETED:
            return _reply(input, "delete-wallet-account", "DONE", account)
        if account["company_id"] != company_id:
            raise _problem(409, "conflict", "the wallet account belongs to another company")
        return _reply(input, "delete-wallet-account", "RUNNING", _continue_deletion(account))


def _continue_deletion(account: dict) -> dict:
    """README 8.3 steps 4-5: delete a FAILED account at once, otherwise order (or keep waiting for) the deletion."""
    if account["status"] == FAILED:
        return _delete(account)
    if not providers.get(account["provider"]).deletion_is_async:
        return _order_deletion(account)
    if account["status"] == ACTIVE:
        account["status"] = DELETING
        _save(account)
    if not account.get("deletion_ordered_at"):
        account = _order_deletion(account)
    return account


# ------------------------------------------------------------------------------ SAP DIV callbacks
def _callback_account(reference: str) -> dict:
    account = service.get_store().get_account_by_ref(reference)
    if account is None:
        raise _problem(404, "not-found", "no wallet account with this externalId")
    return account


def accept_account_created(reference: str, body: dict, claims: dict | str | None) -> None:
    """README 7.6 `POST /callbacks/sap-div/technical-users/{externalId}`; the route answers 204. Every accepted
    callback, also a duplicate, is audited."""
    details = body if isinstance(body, dict) else {}
    for name in ("authenticationServiceUrl", "clientID", "clientSecret"):
        if not isinstance(details.get(name), str) or not details[name]:
            raise _problem(400, "validation", f"{name} is required")
    found = _callback_account(reference)
    with _lock(found["technical_user_id"]):
        account = _callback_account(reference)
        if account["status"] == REQUESTED:
            _activate(account, details["authenticationServiceUrl"].rstrip("/") + "/oauth/token",
                      details["clientID"], details["clientSecret"])
        elif account["status"] != ACTIVE:
            raise _problem(409, "invalid-state", "the wallet account is not waiting for this callback")
        service.audit(claims, "SUBMIT_WALLET_ACCOUNT_CALLBACK", account["company_id"], account["id"])


def accept_account_deleted(reference: str, claims: dict | str | None) -> None:
    """README 7.6 `POST /callbacks/sap-div/technical-users/{externalId}/delete`; the route answers 204."""
    found = _callback_account(reference)
    with _lock(found["technical_user_id"]):
        account = _callback_account(reference)
        if account["status"] == DELETING:
            _delete(account)
        elif account["status"] != DELETED:
            raise _problem(409, "invalid-state", "the wallet account is not being deleted")
        service.audit(claims, "SUBMIT_WALLET_ACCOUNT_CALLBACK", account["company_id"], account["id"])


# ------------------------------------------------------------------------------ credentials (7.3)
def retrieve_credentials(technical_user_id: str, claims: dict) -> WalletAccountCredentials:
    """`POST /technical-users/{id}/wallet-account/credentials` (README 7.3): hands the credentials out exactly
    once. Reading, deleting the row, `RETRIEVED` and the audit entry happen under the lock of the technical user."""
    store = service.get_store()
    with _lock(technical_user_id):
        account = _current(technical_user_id)
        if not claims.get("company_id") or claims["company_id"] != account["company_id"]:
            raise _problem(404, "not-found", "no wallet account for this technical user")
        if account["status"] != ACTIVE:
            raise _problem(409, "invalid-state", "the wallet account is not ACTIVE")
        state = account["credentials_state"]
        if state == RETRIEVED:
            raise _problem(410, "already-retrieved", "the credentials were retrieved already")
        if state == EXPIRED:
            raise _problem(410, "credentials-expired", "the credentials were deleted after the retention period")
        if state != AVAILABLE:
            raise _problem(409, "no-credentials", "the wallet account has no credentials to retrieve")
        row = store.get_account_credentials(account["id"])
        if row is None:
            raise _problem(410, "already-retrieved", "the credentials were retrieved already")
        # Decrypt before the row is removed: a failing key must not destroy credentials nobody has received.
        secret = crypto.decrypt(row["client_secret_encrypted"], row["nonce"], row["key_version"])
        if store.pop_account_credentials(account["id"]) is None:
            raise _problem(410, "already-retrieved", "the credentials were retrieved already")
        account["credentials_state"] = RETRIEVED
        _save(account)
        service.audit(claims, "RETRIEVE_WALLET_CREDENTIALS", account["company_id"], account["id"])
        wallet = service.get_wallet(account["company_id"]) or {}
        return WalletAccountCredentials(wallet_account_ref=account["id"], token_url=row["token_url"],
                                        client_id=row["client_id"], client_secret=secret, did=wallet.get("did"),
                                        credential_service_url=wallet.get("credential_service_url"))


# ------------------------------------------------------------------------------ scheduled tasks
def _deadline_passed(candidate: dict, field: str, moment: dt.datetime) -> bool:
    ordered = service.when(candidate.get(field))
    return ordered is not None and moment - ordered > dt.timedelta(
        minutes=config.provider_callback_timeout_minutes())


def _task_callback_deadline(moment: dt.datetime) -> None:
    """README 6.10: an order older than the deadline. `REQUESTED` becomes `FAILED` (`PROVIDER_TIMEOUT`);
    `DELETING` stays and `WalletAccountDeletionFailed` is published once (open question: no repetition)."""
    store = service.get_store()
    for candidate in store.list_accounts(statuses=[REQUESTED, DELETING]):
        field = "provider_ordered_at" if candidate["status"] == REQUESTED else "deletion_ordered_at"
        if not _deadline_passed(candidate, field, moment):
            continue
        with _lock(candidate["technical_user_id"]):
            account = store.get_account_by_ref(candidate["id"])
            if account is None or account["status"] != candidate["status"]:
                continue
            if account["status"] == REQUESTED:
                _fail(account, "PROVIDER_TIMEOUT")
            elif not account.get("deletion_failed_at"):
                account["deletion_failed_at"] = moment
                _save(account)
                _publish("WalletAccountDeletionFailed", account, reason="PROVIDER_TIMEOUT")


def _task_credentials_retention(moment: dt.datetime) -> None:
    """README 6.10, 6.7: credentials that were not retrieved are deleted once `expires_at` is reached."""
    store = service.get_store()
    for candidate in store.list_accounts():
        row = store.get_account_credentials(candidate["id"]) if candidate["credentials_state"] == AVAILABLE else None
        expires = service.when(row["expires_at"]) if row else None
        if expires is None or expires > moment:
            continue
        with _lock(candidate["technical_user_id"]):
            account = store.get_account_by_ref(candidate["id"])
            if account is not None and account["credentials_state"] == AVAILABLE:
                store.delete_account_credentials(account["id"])
                account["credentials_state"] = EXPIRED
                _save(account)


def run_tasks() -> None:
    """The account part of the scheduled tasks; `service.run_timer_once()` calls it."""
    _task_callback_deadline(service.now())
    _task_credentials_retention(service.now())


providers.on_callback("account-created", accept_account_created)
providers.on_callback("account-deleted", accept_account_deleted)

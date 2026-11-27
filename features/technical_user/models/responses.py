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
#  Assisted-By: Claude Code (claude-opus-5-5)
"""Responses and step results as in `openapi.yaml` (components/schemas).

Optional fields that the spec leaves out (`walletAccountRef` without wallet, the check of an unknown ID) are
left unset, and `to_wire()` drops what is unset: a field that was set to `None` stays `null` in JSON."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from portal_common.models import ApiModel

from . import Origin, Status, SubscriptionParty, Viewer, WalletAccess
from .schemas import RoleRef

__all__ = [
    "AssignableRole", "CompanyTechnicalUsers", "Credentials", "SubscriptionAccount",
    "SubscriptionAccounts", "SubscriptionTechnicalUsers", "TechnicalUser", "TechnicalUserCheck",
    "TechnicalUserSummary", "TechnicalUserWithCredentials", "WalletResult", "WIRE", "to_wire",
]

WIRE = {"response_model_exclude_unset": True}
"""Options of every operation with a `response_model`: the JSON of `to_wire()`."""


def to_wire(value: Any) -> Any:  # noqa: ANN401 (a model, a list or tuple of them, or None)
    """The JSON form of a result for in-process callers; models inside lists and tuples too."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_unset=True)
    if isinstance(value, (list, tuple)):
        return type(value)(to_wire(item) for item in value)
    return value


class TechnicalUserSummary(ApiModel):
    id: str
    company_id: str
    name: str
    description: str | None
    origin: Origin
    offer_subscription_id: str | None
    subscription_party: SubscriptionParty | None
    co_viewer_company_id: str | None
    viewer_role: Viewer
    status: Status
    iam_client_id: str
    wallet_access: WalletAccess
    disabled: bool
    created_at: str
    changed_at: str


class TechnicalUser(TechnicalUserSummary):
    auth_method: Literal["SECRET"]
    roles: list[RoleRef]
    wallet_account_ref: str | None = None


class Credentials(ApiModel):
    """Handed out exactly once and not stored."""

    iam_client_id: str
    secret: str
    token_url: str


class TechnicalUserWithCredentials(TechnicalUser):
    credentials: Credentials


class TechnicalUserCheck(ApiModel):
    exists: bool
    belongs_to_company: bool | None = None
    status: Status | None = None
    origin: Origin | None = None
    wallet_access: WalletAccess | None = None
    disabled: bool | None = None
    usable_for_connector: bool


class AssignableRole(ApiModel):
    name: str
    description: str | None
    grants_wallet_access: bool
    provider_only: bool


class SubscriptionAccount(ApiModel):
    technical_user_id: str
    subscription_party: SubscriptionParty
    iam_client_id: str
    status: Status
    wallet_access: WalletAccess
    roles: list[RoleRef]


class SubscriptionAccounts(ApiModel):
    offer_subscription_id: str
    accounts: list[SubscriptionAccount]


class WalletResult(ApiModel):
    technical_user_id: str
    status: Status
    wallet_access: WalletAccess
    wallet_account_ref: str | None


class CompanyTechnicalUsers(ApiModel):
    company_id: str
    technical_user_ids: list[str]


class SubscriptionTechnicalUsers(ApiModel):
    offer_subscription_id: str
    technical_user_ids: list[str]

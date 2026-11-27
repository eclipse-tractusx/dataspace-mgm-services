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
#################################################################################
"""API models of C4-M2: the request bodies, step inputs and responses of the openapi.yaml, with its JSON field
names. Timestamps stay ISO strings as the services write them, so the wire format does not change."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from portal_common.models import ApiModel, StepRequest, StepResult, Uuid

from .value_sets import (
    CredentialsState,
    IssuanceMode,
    Provider,
    WalletAccountFailureReason,
    WalletAccountStatus,
    WalletFailureReason,
    WalletStatus,
)


# ------------------------------------------------------------------------------------- step inputs
class CreateWalletInput(StepRequest):
    """`StepCreateWallet`. `provider` stays a string: `BRING_YOUR_OWN` and unknown names are answered by the
    service (`provider-not-enabled` or `validation`, README 6.1, 12)."""

    company_id: Uuid
    provider: str | None = None


class WalletAccountInput(StepRequest):
    """`StepWalletAccount` of `create-wallet-account` and `delete-wallet-account`."""

    technical_user_id: Uuid
    company_id: Uuid
    wallet_account_ref: Uuid | None = None


# ---------------------------------------------------------------------------------- step results
class WalletStepResult(ApiModel):
    """`StepResultWallet.result`; optional fields are left out when empty."""

    wallet_id: str
    company_id: str
    provider: Provider
    status: WalletStatus
    did: str | None = None
    did_document_location: str | None = None
    failure_reason: WalletFailureReason | None = None


class WalletAccountStepResult(ApiModel):
    """`StepResultWalletAccount.result`; `walletAccountRef` and `provider` are empty if there never was an account."""

    wallet_account_ref: str | None = None
    technical_user_id: str
    company_id: str
    provider: Provider | None = None
    status: WalletAccountStatus
    failure_reason: WalletAccountFailureReason | None = None


WalletStepReply = StepResult[WalletStepResult]
WalletAccountStepReply = StepResult[WalletAccountStepResult]


# -------------------------------------------------------------------------------------- responses
class Wallet(ApiModel):
    """`Wallet`: the view of the people of the company, without secrets (README 7.1)."""

    company_id: str
    provider: Provider
    status: WalletStatus
    did: str | None = None
    did_document_location: str | None = None
    credential_service_url: str | None = None
    bdrs_url: str | None = None
    sts_token_url: str | None = None
    supports_wallet_accounts: bool
    failure_reason: WalletFailureReason | None = None
    created_at: str | None = None
    activated_at: str | None = None


class WalletInfo(ApiModel):
    """`WalletInfo`: the view of other modules, without secrets (README 9.1)."""

    wallet_id: str
    company_id: str
    bpn: str
    provider: Provider
    provider_ref: str | None = None
    status: WalletStatus
    did: str | None = None
    did_document_location: str | None = None
    credential_service_url: str | None = None
    issuance_mode: IssuanceMode
    supports_wallet_accounts: bool
    failure_reason: WalletFailureReason | None = None
    activated_at: str | None = None


class WalletAccount(ApiModel):
    """`WalletAccount`: the state of the credentials, never the credentials (README 7.2, 9.2)."""

    wallet_account_ref: str
    technical_user_id: str
    company_id: str
    provider: Provider
    status: WalletAccountStatus
    failure_reason: WalletAccountFailureReason | None = None
    credentials_state: CredentialsState
    credentials_expire_at: str | None = None
    created_at: str | None = None
    changed_at: str | None = None


class WalletAccountCredentials(ApiModel):
    """`WalletAccountCredentials`: handed out exactly once (README 7.3)."""

    wallet_account_ref: str
    token_url: str
    client_id: str
    client_secret: str
    did: str | None = None
    credential_service_url: str | None = None


class _HolderAccessBase(ApiModel):
    issuance_mode: IssuanceMode
    company_id: str
    bpn: str
    did: str
    provider: Provider


class HolderAccessIssuerWrites(_HolderAccessBase):
    """`HolderAccessIssuerWrites` (SAP DIV): the issuer writes into the wallet."""

    issuance_mode: Literal["ISSUER_WRITES"] = "ISSUER_WRITES"
    holder: str | None = None
    wallet_url: str
    client_id: str
    client_secret: str


class HolderAccessHolderRequests(_HolderAccessBase):
    """`HolderAccessHolderRequests` (IdentityHub, CSP): the wallet requests the credentials."""

    issuance_mode: Literal["HOLDER_REQUESTS"] = "HOLDER_REQUESTS"
    identity_api_url: str
    participant_context_id: str
    api_key: str
    credential_service_url: str | None = None


HolderAccess = Annotated[HolderAccessIssuerWrites | HolderAccessHolderRequests, Field(discriminator="issuance_mode")]
"""`HolderAccess` (README 9.3), only for C4-M1."""


def to_json(model: ApiModel, *, keep_unset: bool = True) -> dict:
    """The JSON form of a model for in-process callers: camelCase, `null` kept like the HTTP answer. Step results
    leave out the fields that were never set (`keep_unset=False`), as the openapi examples do."""
    return model.model_dump(mode="json", by_alias=True, exclude_unset=not keep_unset)

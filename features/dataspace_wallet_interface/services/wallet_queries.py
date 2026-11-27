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
"""The wallet queries of C4-M2 (README 7.1, 9.1, 9.3): views of the wallet row, without secrets except the holder
access for C4-M1."""
from __future__ import annotations

from ..managers import config
from ..models.api import HolderAccess, HolderAccessHolderRequests, HolderAccessIssuerWrites, Wallet, WalletInfo
from ..models.errors import problem as _problem
from ..models.value_sets import IssuanceMode
from .wallet_service import HOLDER_ACCESS, audit, get_store, iso, wallet_secret


def _issuance_mode(provider: str) -> IssuanceMode:
    return "ISSUER_WRITES" if provider == "SAP_DIV" else "HOLDER_REQUESTS"


def _wallet_or_404(company_id: str) -> dict:
    wallet = get_store().get_wallet(company_id)
    if wallet is None:
        raise _problem(404, "not-found", "no wallet for this company")
    return wallet


def wallet_info(company_id: str) -> WalletInfo:
    """README 9.1 `WalletInfo`: 13 fields, no secrets."""
    wallet = _wallet_or_404(company_id)
    return WalletInfo(wallet_id=wallet["id"], company_id=wallet["company_id"], bpn=wallet["bpn"],
                      provider=wallet["provider"], provider_ref=wallet.get("provider_ref"), status=wallet["status"],
                      did=wallet.get("did"), did_document_location=wallet.get("did_document_location"),
                      credential_service_url=wallet.get("credential_service_url"),
                      issuance_mode=_issuance_mode(wallet["provider"]), supports_wallet_accounts=True,
                      failure_reason=wallet.get("failure_reason"), activated_at=iso(wallet.get("activated_at")))


def wallet_view(company_id: str) -> Wallet:
    """README 7.1 openapi `Wallet`: the view of the people of the company, no secrets."""
    wallet = _wallet_or_404(company_id)
    return Wallet(company_id=wallet["company_id"], provider=wallet["provider"], status=wallet["status"],
                  did=wallet.get("did"), did_document_location=wallet.get("did_document_location"),
                  credential_service_url=wallet.get("credential_service_url"), bdrs_url=config.bdrs_public_url(),
                  sts_token_url=config.identityhub_sts_token_url() if wallet["provider"] == "IDENTITY_HUB" else None,
                  supports_wallet_accounts=True, failure_reason=wallet.get("failure_reason"),
                  created_at=iso(wallet.get("created_at")), activated_at=iso(wallet.get("activated_at")))


def holder_access(company_id: str, claims: dict | str | None = None) -> HolderAccess:
    """README 9.3 for C4-M1: how credentials get into the wallet, with the access needed for that.
    `claims` are the token claims over HTTP; in the same process the entry holds the name of C4-M1."""
    wallet = _wallet_or_404(company_id)
    if wallet["status"] != "ACTIVE":
        raise _problem(409, "wallet-not-active", "the wallet is not ACTIVE")
    access = wallet_secret(wallet["id"], HOLDER_ACCESS)
    if access is None:
        raise _problem(409, "wallet-not-active", "the wallet has no holder access")
    base = {"company_id": wallet["company_id"], "bpn": wallet["bpn"], "did": wallet["did"],
            "provider": wallet["provider"]}
    access_model: HolderAccessIssuerWrites | HolderAccessHolderRequests
    if wallet["provider"] == "SAP_DIV":
        access_model = HolderAccessIssuerWrites(**base, holder=wallet["did_document_location"],
                                                wallet_url=access["url"], client_id=access["client_id"],
                                                client_secret=access["secret"])
    else:
        access_model = HolderAccessHolderRequests(**base, identity_api_url=access["url"],
                                                  participant_context_id=access["client_id"], api_key=access["secret"],
                                                  credential_service_url=wallet.get("credential_service_url"))
    audit(claims if claims is not None else "c4-m1", "READ_HOLDER_ACCESS", wallet["company_id"], wallet["id"])
    return access_model

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
"""In-process contract of the dataspace wallets (call convention, AGENTS.md): the steps of README 8 and the queries
of README 9 under their convention names. Other modules and Process Orchestration import only from here; the logic
lives in `services/`.

Provider: SAP DIV, IdentityHub or the dataspace wallet of the CSP (`managers/providers/`, README 6.1, 6.11). The
holder access (API key or client secret) is stored encrypted and only returned by the query for C4-M1. The
services return the models of `models/api.py`; this contract answers their JSON form (camelCase dicts).
"""
from __future__ import annotations

from portal_common import standin

from .models import MODULE
from .models.api import to_json
from .services import account_service, callback_service, wallet_queries, wallet_service

__all__ = [
    "MODULE", "create_wallet", "create_wallet_account", "delete_wallet_account", "get_holder_access",
    "get_wallet_account_internal", "get_wallet_info", "reset", "retrieve_wallet_account_credentials",
    "sap_div_wallet_account_created", "sap_div_wallet_account_deleted", "sap_div_wallet_created", "store",
    "view_wallet_account", "wallet_view",
]


def store() -> wallet_service.WalletStore:
    """The active store."""
    return wallet_service.get_store()


def reset() -> None:
    """Empty the tables, the key cache and the state of the provider stand-ins."""
    wallet_service.reset()


# -- steps for Process Orchestration (README 8): input = JSON body incl. processId and stepRunId ---
def create_wallet(input: dict) -> dict:
    """Step `create-wallet` (README 8.1)."""
    return to_json(wallet_service.create_wallet(input), keep_unset=False)


def create_wallet_account(input: dict) -> dict:
    """Step `create-wallet-account` (README 8.2)."""
    return to_json(account_service.create_wallet_account(input), keep_unset=False)


def delete_wallet_account(input: dict) -> dict:
    """Step `delete-wallet-account` (README 8.3)."""
    return to_json(account_service.delete_wallet_account(input), keep_unset=False)


# -- queries for other modules (README 9): parameters by their openapi names ------------------------
def get_wallet_info(*, companyId: str) -> dict:
    """Query `getWalletInfo` (README 9.1): the wallet without secrets."""
    return to_json(wallet_queries.wallet_info(companyId))


def wallet_view(*, companyId: str) -> dict:
    """Body of `GET /companies/{companyId}/wallet` (README 7.1, openapi `Wallet`)."""
    return to_json(wallet_queries.wallet_view(companyId))


def get_holder_access(*, companyId: str, claims: dict | None = None) -> dict:
    """Query `getHolderAccess` (README 9.3), only for C4-M1. `claims` is set by the HTTP route; in the same
    process the audit entry holds the name of the calling module."""
    return to_json(wallet_queries.holder_access(companyId, claims))


def get_wallet_account_internal(*, technicalUserId: str) -> dict:
    """Query `getWalletAccountInternal` (README 9.2)."""
    return to_json(account_service.get_wallet_account_internal(technicalUserId=technicalUserId))


# -- operations of people and providers, only called by the controllers ------------------------------
def view_wallet_account(technical_user_id: str, claims: dict) -> dict:
    """`GET /technical-users/{technicalUserId}/wallet-account` (README 7.2), scope `company`."""
    return to_json(account_service.view_wallet_account(technical_user_id, claims))


def retrieve_wallet_account_credentials(technical_user_id: str, claims: dict) -> dict:
    """`POST /technical-users/{technicalUserId}/wallet-account/credentials` (README 7.3): exactly once."""
    return to_json(account_service.retrieve_credentials(technical_user_id, claims))


def sap_div_wallet_created(bpn: str, body: dict, claims: dict) -> None:
    """SAP DIV callback: the wallet is created (README 7.6)."""
    callback_service.wallet_created(bpn, body, claims)


def sap_div_wallet_account_created(external_id: str, body: dict, claims: dict) -> None:
    """SAP DIV callback: the wallet account is created (README 7.6)."""
    callback_service.account_created(external_id, body, claims)


def sap_div_wallet_account_deleted(external_id: str, claims: dict) -> None:
    """SAP DIV callback: the wallet account is deleted (README 7.6)."""
    callback_service.account_deleted(external_id, claims)


__getattr__ = standin.missing_interface(MODULE)   # steps and queries not implemented yet: stand-in

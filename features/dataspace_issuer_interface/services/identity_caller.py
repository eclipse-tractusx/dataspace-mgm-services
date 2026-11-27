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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""Resolve company wallet access through C4-M2 and start IdentityHub issuance."""

from __future__ import annotations

from pydantic import ValidationError

from portal_common import neighbours
from portal_common.problems import Problem

from ..exceptions.interface_api_error import InterfaceApiError
from ..managers.identity_service_http_client import IdentityServiceHttpClient
from ..models.credential_issuance_request import CredentialIssuanceRequest
from ..models.wallet_credential_request import WalletCredentialRequest


class IdentityCaller:
    """Fetch holder access from C4-M2, then trigger wallet-side DCP issuance."""

    def __init__(self, client: IdentityServiceHttpClient | None = None):
        self._client = client or IdentityServiceHttpClient()

    def request_credential(self, request: CredentialIssuanceRequest) -> str:
        """Fetch this company's holder access from C4-M2, then ask its IdentityHub to issue."""
        try:
            access = neighbours.query(
                "c4-m1", "c4-m2", "get_holder_access", companyId=request.company_id
            )
        except Problem as error:
            raise InterfaceApiError(502, f"C4-M2 holder-access query failed: {error.name}") from error
        if access is None:
            raise InterfaceApiError(404, "No holder wallet access found for this company")
        if not isinstance(access, dict):
            raise InterfaceApiError(502, "C4-M2 returned invalid holder access")
        if access.get("issuanceMode") != "HOLDER_REQUESTS":
            raise InterfaceApiError(409, "The company wallet does not support holder-requested issuance")

        try:
            wallet_request = WalletCredentialRequest(
                identity_api_url=access["identityApiUrl"],
                identity_api_version=request.identity_api_version,
                participant_context_id=access["participantContextId"],
                api_key=access["apiKey"],
                issuer_did=request.issuer_did,
                holder_pid=request.holder_pid,
                credential_definition=request.credential_definition,
                credential_type=request.credential_type,
                credential_format=request.credential_format,
            )
        except (KeyError, TypeError, ValidationError) as error:
            raise InterfaceApiError(502, "C4-M2 returned invalid holder access") from error

        return self._client.request_credential(wallet_request)


identity_caller = IdentityCaller()

__all__ = ["IdentityCaller", "identity_caller"]

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
"""HTTP calls used by the optional IssuerService caller."""

from __future__ import annotations

from urllib.parse import quote

from ..exceptions.issuer_caller_error import IssuerCallerError
from ..models.holder_registration import HolderRegistration
from ..util.http import _request
from .issuer_service_configuration import IssuerServiceConfiguration


class IssuerServiceHttpClient:
    """Sends holder-admin calls and the wallet-side issuance trigger."""

    def __init__(self, configuration: IssuerServiceConfiguration | None = None):
        self._configuration = configuration or IssuerServiceConfiguration()

    def register_holder(self, request: HolderRegistration) -> None:
        """Register the company wallet DID in the issuer participant context."""
        _request(
            "IssuerService",
            "POST",
            f"{self._configuration.admin_participant_url()}/holders",
            headers={"x-api-key": self._configuration.get_env("ISSUER_SERVICE_API_KEY")},
            body=request.to_json(),
            accepted=(409,),
        )

    def get_holders(self) -> list[dict[str, object]]:
        """Return holder metadata registered in the issuer participant context."""
        response = _request(
            "IssuerService",
            "POST",
            f"{self._configuration.admin_participant_url()}/holders/query",
            headers={"x-api-key": self._configuration.get_env("ISSUER_SERVICE_API_KEY")},
            body={},
        )
        try:
            holders = response.json()
        except ValueError as error:
            raise IssuerCallerError("IssuerService returned invalid holder data", retryable=False) from error
        if not isinstance(holders, list) or not all(isinstance(holder, dict) for holder in holders):
            raise IssuerCallerError("IssuerService returned invalid holder data", retryable=False)
        return holders

    def get_holder(self, holder_id: str) -> dict[str, object]:
        """Return one holder registered in the issuer participant context."""
        response = _request(
            "IssuerService",
            "GET",
            f"{self._configuration.admin_participant_url()}/holders/{quote(holder_id, safe='')}",
            headers={"x-api-key": self._configuration.get_env("ISSUER_SERVICE_API_KEY")},
        )
        try:
            holder = response.json()
        except ValueError as error:
            raise IssuerCallerError("IssuerService returned invalid holder data", retryable=False) from error
        if not isinstance(holder, dict):
            raise IssuerCallerError("IssuerService returned invalid holder data", retryable=False)
        return holder


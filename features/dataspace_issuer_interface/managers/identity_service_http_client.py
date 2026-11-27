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
"""HTTP client for starting credential issuance through IdentityHub."""

from __future__ import annotations

import re

from ..exceptions.interface_api_error import InterfaceApiError
from ..exceptions.issuer_caller_error import IssuerCallerError
from ..models.wallet_credential_request import WalletCredentialRequest
from ..util.http import _request
from .issuer_service_configuration import IssuerServiceConfiguration


class IdentityServiceHttpClient:
    """Sends the credential request to the selected company's IdentityHub."""

    def __init__(self, configuration: IssuerServiceConfiguration | None = None):
        self._configuration = configuration or IssuerServiceConfiguration()

    def _wallet_request_url(self, request: WalletCredentialRequest) -> str:
        base = request.identity_api_url.rstrip("/")
        if not re.search(r"/v\d+[a-z0-9]*$", base):
            version = request.identity_api_version or self._configuration.get_env(
                "ISSUER_SERVICE_API_VERSION", "v1beta"
            )
            base = f"{base}/{version.strip('/')}"
        return f"{base}/participants/{request.participant_context_id}/credentials/request"

    @staticmethod
    def _upstream_error(error: IssuerCallerError) -> InterfaceApiError:
        """Map a wallet HTTP failure to the standalone API's status and detail."""
        status_code = 502 if error.retryable else 409
        return InterfaceApiError(status_code, str(error))

    def request_credential(self, request: WalletCredentialRequest) -> str:
        """Tell IdentityHub to start DCP issuance for this holder wallet."""
        try:
            _request(
                "IdentityHub",
                "POST",
                self._wallet_request_url(request),
                headers={"x-api-key": request.api_key.get_secret_value()},
                body=request.to_json(),
            )
        except IssuerCallerError as error:
            raise self._upstream_error(error) from error
        return request.holder_pid

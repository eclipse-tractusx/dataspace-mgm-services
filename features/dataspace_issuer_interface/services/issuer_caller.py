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
"""Business boundary for IssuerService holder setup and wallet-side issuance."""

from __future__ import annotations

from ..exceptions.issuer_caller_error import IssuerCallerError
from ..managers.issuer_service_http_client import IssuerServiceHttpClient
from ..models.holder_registration import HolderRegistration


class IssuerCaller:
    """Coordinates stateless IssuerService and holder-wallet HTTP calls."""

    def __init__(self, client: IssuerServiceHttpClient | None = None):
        self._client = client or IssuerServiceHttpClient()

    def register_holder(self, request: HolderRegistration) -> None:
        self._client.register_holder(request)

    def get_holders(self) -> list[dict[str, object]]:
        return self._client.get_holders()

    def get_holder(self, holder_id: str) -> dict[str, object]:
        return self._client.get_holder(holder_id)


issuer_caller = IssuerCaller()


__all__ = ["IssuerCaller", "IssuerCallerError", "issuer_caller"]

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
"""The body checks of the SAP DIV wallet callback (README 7.6, openapi `SapDivWalletCallback`).

They are plain checks, not a request model: README 7.6 answers a malformed body with 400, but an invalid DID document
with 204 and the wallet `FAILED` (`INVALID_DID_DOCUMENT`)."""
from __future__ import annotations


def callback_body_problem(body: object) -> str | None:
    """Why a callback body is malformed (openapi `SapDivWalletCallback`), None if it is complete."""
    if not isinstance(body, dict) or not isinstance(body.get("did"), str) or not body["did"]:
        return "did is required"
    if not isinstance(body.get("didDocument"), dict):
        return "didDocument is required"
    details = body.get("authenticationDetails")
    if not isinstance(details, dict):
        return "authenticationDetails is required"
    for name in ("authenticationServiceUrl", "clientID", "clientSecret"):
        if not isinstance(details.get(name), str) or not details[name]:
            return f"authenticationDetails.{name} is required"
    return None


def callback_document_valid(document: dict) -> bool:
    """README 7.6 step 4: schema of Portal 2.6.0, `@context` list, `id`, `service` list with `id` and `type`,
    `verificationMethod` list with `id`, `type` and `publicKeyJwk` with `kty`, `crv`, `x`, `y`."""
    def text(value: object) -> bool:
        return isinstance(value, str) and value != ""
    if not isinstance(document.get("@context"), list) or not text(document.get("id")):
        return False
    services, methods = document.get("service"), document.get("verificationMethod")
    if not isinstance(services, list) or not isinstance(methods, list):
        return False
    if not all(isinstance(e, dict) and text(e.get("id")) and e.get("type") for e in services):
        return False
    for method in methods:
        jwk = method.get("publicKeyJwk") if isinstance(method, dict) else None
        if not (text(method.get("id")) if isinstance(method, dict) else False) or not method.get("type") \
                or not isinstance(jwk, dict) or not all(text(jwk.get(k)) for k in ("kty", "crv", "x", "y")):
            return False
    return True

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
"""Status reports of the issuers (README 7.4), called over HTTP by the Credential Issuer and the CSP issuer."""
from __future__ import annotations

from fastapi import Body
from fastapi.responses import Response

from features.credentials import interface
from portal_common.routing import Controller, Permission

controller = Controller("Credentials: Issuer Callbacks")


@controller.post("/{credentialKind}", status_code=204, response_class=Response, summary="Status report of an issuer")
def issuer_callback(credentialKind: str, body: object = Body(...), claims: dict = Permission) -> Response:
    """README 7.4: token and permission (dependency), kind, then the body (`IssuerResponse`), so the body is
    validated in the service after the kind; row handling, audit entry, 204 without body."""
    interface.receive_report(credentialKind, body, claims)
    return Response(status_code=204)

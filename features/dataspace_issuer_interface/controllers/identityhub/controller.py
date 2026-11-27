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
"""Start credential issuance through a company's IdentityHub wallet.

This endpoint calls the selected IdentityHub Identity API. IdentityHub then
initiates the DCP issuance exchange with the issuer and stores the delivered
credential in the company's wallet. This controller does not issue the VC.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...models.credential_issuance_request import CredentialIssuanceRequest
from ...services.identity_caller import identity_caller

router = APIRouter(tags=["Dataspace Issuer Interface: Credentials"])


@router.post("/credentials/request", status_code=202)
def request_credential(
    request: CredentialIssuanceRequest,
) -> dict[str, str]:
    """Ask IdentityHub to start DCP issuance for this wallet and credential."""
    holder_pid = identity_caller.request_credential(request)
    return {"holderPid": holder_pid}

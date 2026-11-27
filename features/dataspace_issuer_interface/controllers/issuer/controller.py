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
"""Expose holder registration through the IssuerService Issuer Admin API.

This endpoint delegates to the configured IssuerService participant-admin
``POST .../holders`` endpoint, authenticating with the IssuerService API key.
Onboarding calls it after the company wallet DID is available. It registers
holder metadata only; IdentityHub starts DCP issuance separately.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from ...models.holder_registration import HolderRegistration
from ...services.issuer_caller import issuer_caller

router = APIRouter(tags=["Dataspace Issuer Interface: Issuer Admin"])


@router.post("/holders", status_code=204)
def register_holder(request: HolderRegistration) -> Response:
    """Delegate holder registration to the IssuerService participant-admin API."""
    issuer_caller.register_holder(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

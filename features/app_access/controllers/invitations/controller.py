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
#  Assisted-By: GitHub Copilot
#################################################################################
"""Acceptance of an invitation by the invited person (README 7.10), scope `own`: with the code, or with a
verification attestation of the EBW-Connector about a mandate of the company (6.8a)."""
from __future__ import annotations

from fastapi import Body

from features.app_access.interface import services
from features.app_access.models import AcceptInvitationResult
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Permission

controller = Controller("App Access: Invitations")


@controller.post("/accept", operation_id="acceptInvitation", response_model=AcceptInvitationResult,
                 summary="Accept an invitation with the code or with a mandate")
@translated
def accept_invitation(body: dict = Body(...), claims: dict = Permission) -> AcceptInvitationResult:
    # Scope `own`: the service acts only on the account of `sub` in the claims (README 7.10).
    return services().invitations.accept(body, claims)

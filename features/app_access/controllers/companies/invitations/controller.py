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
"""Invitations of the company by its Company Admin (README 7.7 to 7.9), scope `company`."""
from __future__ import annotations

from fastapi import Body, Query

from features.app_access.interface import company_actor, services
from features.app_access.models import Invitation, InvitationWithCode
from features.app_access.models import Page as Paged
from features.app_access.models.constants import InvitationKind
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("App Access: Company Invitations")


@controller.get("", operation_id="listInvitations", response_model=Paged[Invitation],
                summary="List the invitations of the company")
@translated
def list_invitations(companyId: str, page: int = Page, size: int = Size,
                     status: list[str] | None = Query(None, description="May be given several times."),
                     claims: dict = Permission) -> Paged[Invitation]:
    company_actor(claims, companyId)
    return services().invitations.list(InvitationKind.COMPANY, companyId, status, page, size)


@controller.post("", status_code=201, operation_id="createInvitation", response_model=InvitationWithCode,
                 summary="Invite a person to the company")
@translated
def create_invitation(companyId: str, body: dict = Body(...), claims: dict = Permission) -> InvitationWithCode:
    actor = company_actor(claims, companyId)
    return services().invitations.create(InvitationKind.COMPANY, companyId, body, actor, "createInvitation")


@controller.delete("/{invitationId}", status_code=204, response_model=None, operation_id="revokeInvitation",
                   summary="Revoke an open invitation")
@translated
def revoke_invitation(companyId: str, invitationId: str, claims: dict = Permission) -> None:
    actor = company_actor(claims, companyId)
    services().invitations.revoke(InvitationKind.COMPANY, companyId, invitationId, actor, "revokeInvitation")

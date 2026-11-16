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
"""Invitations of OSP staff (README 7.17 to 7.19), scope `osp`."""
from __future__ import annotations

from fastapi import Body, Query, Response

from features.app_access.interface import osp_actor, services
from features.app_access.models import Invitation, InvitationWithCode, Page as Paged
from features.app_access.models.constants import InvitationKind
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("App Access: OSP Staff Invitations")


@controller.get("", operation_id="listStaffInvitations", response_model=Paged[Invitation],
                summary="List the staff invitations")
@translated
def list_staff_invitations(page: int = Page, size: int = Size,
                           status: list[str] | None = Query(None, description="May be given several times."),
                           claims: dict = Permission) -> Paged[Invitation]:
    return services().invitations.list(InvitationKind.STAFF, None, status, page, size)


@controller.post("", status_code=201, operation_id="createStaffInvitation", response_model=InvitationWithCode,
                 summary="Invite a person as OSP staff")
@translated
def create_staff_invitation(body: dict = Body(...),
                            claims: dict = Permission) -> InvitationWithCode:
    return services().invitations.create(InvitationKind.STAFF, None, body, osp_actor(claims), "createStaffInvitation")


@controller.delete("/{invitationId}", status_code=204, operation_id="revokeStaffInvitation",
                   summary="Revoke an open staff invitation")
@translated
def revoke_staff_invitation(invitationId: str, claims: dict = Permission) -> Response:
    services().invitations.revoke(InvitationKind.STAFF, None, invitationId, osp_actor(claims),
                                  "revokeStaffInvitation")
    return Response(status_code=204)

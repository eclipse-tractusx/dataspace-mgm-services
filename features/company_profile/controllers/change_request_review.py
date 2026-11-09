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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Company profile: OSP staff review change requests (README 7.14 to 7.18).
"""
from __future__ import annotations

from fastapi import Body, Query, Response

from features.company_profile.services import change_request_service
from features.company_profile.services.shared import MODULE
from portal_common.routing import controller_router, permission

router = controller_router(MODULE, "Company Profile: Change Request Review")


# --------------------------------------------------------------------- change requests, review (7.14 - 7.18)
@router.get("/osp/change-requests")
def list_change_requests(status: list[str] | None = Query(None), companyId: str | None = None,
                         page: int = 0, size: int = 20,
                         _: dict = permission(MODULE, "GET", "/osp/change-requests")):
    return change_request_service.list_change_requests(status=status, companyId=companyId, page=page, size=size)


@router.get("/osp/change-requests/{changeRequestId}")
def get_change_request(changeRequestId: str,
                       _: dict = permission(MODULE, "GET", "/osp/change-requests/{changeRequestId}")):
    return change_request_service.get_change_request(changeRequestId)


@router.get("/osp/change-requests/{changeRequestId}/documents/{documentId}")
def get_change_request_document(changeRequestId: str, documentId: str,
                                claims: dict = permission(
                                    MODULE, "GET",
                                    "/osp/change-requests/{changeRequestId}/documents/{documentId}")):
    answer = change_request_service.get_change_request_document(changeRequestId, documentId, claims.get("sub"))
    return Response(answer["content"], media_type=answer["media_type"], headers={
        "Content-Disposition": f'attachment; filename="{answer["file_name"]}"'})


@router.post("/osp/change-requests/{changeRequestId}/approve")
def approve_change_request(changeRequestId: str, body: dict | None = Body(None),
                           claims: dict = permission(
                               MODULE, "POST", "/osp/change-requests/{changeRequestId}/approve")):
    return change_request_service.approve_change_request(changeRequestId, body, claims.get("sub"))


@router.post("/osp/change-requests/{changeRequestId}/decline")
def decline_change_request(changeRequestId: str, body: dict | None = Body(None),
                           claims: dict = permission(
                               MODULE, "POST", "/osp/change-requests/{changeRequestId}/decline")):
    return change_request_service.decline_change_request(changeRequestId, body, claims.get("sub"))

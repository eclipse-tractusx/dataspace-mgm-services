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
"""Company profile: change requests of the own company (README 7.4 to 7.6), scope `company`.
"""
from __future__ import annotations

import json

from fastapi import File, Form, UploadFile

from features.company_profile.services import change_request_service
from features.company_profile.services.shared import MODULE
from portal_common.problems import Problem
from portal_common.routing import company_scope, controller_router, permission

router = controller_router(MODULE, "Company Profile: Change Requests")


# ------------------------------------------------------------------------------ change requests (7.4 - 7.6)
@router.post("/companies/{companyId}/change-requests", status_code=201)
def create_change_request(companyId: str, data: str = Form(...),
                          documents: list[UploadFile] = File(default=[]),
                          claims: dict = permission(MODULE, "POST",
                                                      "/companies/{companyId}/change-requests")):
    company_scope(MODULE, claims, companyId)
    try:
        parsed = json.loads(data)
    except ValueError as error:
        raise Problem(MODULE, 400, "validation",
                      errors=[{"field": "data", "reason": f"not JSON: {error}"}]) from error
    files = [(upload.filename or "", upload.file.read(), upload.content_type) for upload in documents]
    return change_request_service.create_change_request(companyId, parsed, files, claims.get("sub"))


@router.get("/companies/{companyId}/change-requests")
def list_own_change_requests(companyId: str, page: int = 0, size: int = 20,
                             claims: dict = permission(MODULE, "GET",
                                                         "/companies/{companyId}/change-requests")):
    company_scope(MODULE, claims, companyId)
    return change_request_service.list_own_change_requests(companyId, page, size)


@router.post("/companies/{companyId}/change-requests/{changeRequestId}/withdraw")
def withdraw_change_request(companyId: str, changeRequestId: str,
                            claims: dict = permission(
                                MODULE, "POST",
                                "/companies/{companyId}/change-requests/{changeRequestId}/withdraw")):
    company_scope(MODULE, claims, companyId)
    return change_request_service.withdraw_change_request(companyId, changeRequestId, claims.get("sub"))

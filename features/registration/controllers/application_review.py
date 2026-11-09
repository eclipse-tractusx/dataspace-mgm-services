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
"""Registration: OSP staff read the applications and their documents (README 7.12 to 7.14).
"""
from __future__ import annotations

from fastapi import Query

from features.registration.models.value_sets import Kind, Status, Verification
from features.registration.services import application_service, application_views, document_service
from features.registration.services.shared import MODULE
from portal_common.routing import Page, Size, controller_router, download, permission

router = controller_router(MODULE, "Registration: Application Review")


# ---------------------------------------------------------------------- OSP staff (7.12 to 7.16)
@router.get("/osp/applications")
def list_all_applications(status: list[Status] | None = Query(None), kind: list[Kind] | None = Query(None),
                          verification: list[Verification] | None = Query(None), companyId: str | None = None,
                          page: int = Page, size: int = Size, _: dict = permission(MODULE, "GET", "/osp/applications")):
    return application_service.list_all(status, kind, verification, companyId, page, size)


@router.get("/osp/applications/{applicationId}")
def get_any_application(applicationId: str, _: dict = permission(MODULE, "GET", "/osp/applications/{applicationId}")):
    return application_views.with_review(application_service.any_application(applicationId))


@router.get("/osp/applications/{applicationId}/documents/{documentId}")
def get_any_document(applicationId: str, documentId: str,
                     claims: dict = permission(MODULE, "GET", "/osp/applications/{applicationId}/documents/{documentId}")):
    return download(*document_service.staff_document(applicationId, documentId, claims["sub"]))

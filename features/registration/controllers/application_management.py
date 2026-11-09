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
"""Registration: the applicant's own applications and supporting documents (README 7.2 to 7.11).

The scope `own` is applied by the services, which answer 404 for other people (README 6.3).
"""
from __future__ import annotations

from fastapi import Body, File, Form, Query, Response, UploadFile

from features.registration.models.value_sets import Status
from features.registration.services import application_service, application_views, document_service
from features.registration.services.shared import MODULE
from portal_common.routing import Page, Size, controller_router, download, permission

router = controller_router(MODULE, "Registration: Applications")


# --------------------------------------------------------------------- applications (7.2 to 7.11)
@router.post("/applications", status_code=201)
def create_application(response: Response, body: dict = Body(...),
                       claims: dict = permission(MODULE, "POST", "/applications")):
    application, created = application_service.create_application(body, claims)
    if created:
        response.headers["Location"] = f"{router.prefix}/applications/{application['id']}"
    else:
        response.status_code = 200
    return application


@router.get("/applications")
def list_applications(status: list[Status] | None = Query(None), page: int = Page, size: int = Size,
                      claims: dict = permission(MODULE, "GET", "/applications")):
    return application_service.list_own(claims["sub"], status, page, size)


@router.get("/applications/{applicationId}")
def get_application(applicationId: str, claims: dict = permission(MODULE, "GET", "/applications/{applicationId}")):
    return application_views.with_review(application_service.own(claims["sub"], applicationId))


@router.patch("/applications/{applicationId}")
def update_application(applicationId: str, body: dict = Body(...),
                       claims: dict = permission(MODULE, "PATCH", "/applications/{applicationId}")):
    return application_service.update_application(applicationId, claims["sub"], body)


@router.put("/applications/{applicationId}/attestation")
def replace_attestation(applicationId: str, body: dict = Body(...),
                        claims: dict = permission(MODULE, "PUT", "/applications/{applicationId}/attestation")):
    return application_service.replace_attestation(applicationId, claims, body.get("attestation"))


@router.post("/applications/{applicationId}/submit")
def submit_application(applicationId: str, body: dict = Body(...),
                       claims: dict = permission(MODULE, "POST", "/applications/{applicationId}/submit")):
    return application_service.submit_application(applicationId, claims["sub"], body)


@router.post("/applications/{applicationId}/withdraw")
def withdraw_application(applicationId: str,
                         claims: dict = permission(MODULE, "POST", "/applications/{applicationId}/withdraw")):
    return application_service.withdraw_application(applicationId, claims["sub"])


@router.post("/applications/{applicationId}/documents", status_code=201)
def upload_document(applicationId: str, response: Response, file: UploadFile = File(...), documentType: str = Form(...),
                    claims: dict = permission(MODULE, "POST", "/applications/{applicationId}/documents")):
    try:
        content = file.file.read(document_service.document_max_bytes() + 1)
    finally:
        file.file.close()
    info = document_service.upload_document(applicationId, claims["sub"], documentType, file.filename, content)
    response.headers["Location"] = f"{router.prefix}/applications/{applicationId}/documents/{info['documentId']}"
    return info


@router.get("/applications/{applicationId}/documents/{documentId}")
def get_document(applicationId: str, documentId: str,
                 claims: dict = permission(MODULE, "GET", "/applications/{applicationId}/documents/{documentId}")):
    return download(*document_service.document(application_service.own(claims["sub"], applicationId), documentId))


@router.delete("/applications/{applicationId}/documents/{documentId}", status_code=204)
def delete_document(applicationId: str, documentId: str,
                    claims: dict = permission(MODULE, "DELETE", "/applications/{applicationId}/documents/{documentId}")):
    document_service.delete_document(applicationId, documentId, claims["sub"])

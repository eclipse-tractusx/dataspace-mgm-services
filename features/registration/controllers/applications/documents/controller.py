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
"""Supporting documents of an own application (README 7.7 to 7.9), scope `own`."""
from __future__ import annotations

from fastapi import File, Form, Request, Response, UploadFile

from features.registration.services import application_service, document_service
from portal_common.routing import Controller, Permission, download

controller = Controller("Registration: Applications")


@controller.post("", status_code=201)
def upload_document(applicationId: str, request: Request, response: Response, file: UploadFile = File(...),
                    documentType: str = Form(...), claims: dict = Permission):
    try:
        content = file.file.read(document_service.document_max_bytes() + 1)
    finally:
        file.file.close()
    info = document_service.upload_document(applicationId, claims["sub"], documentType, file.filename, content)
    response.headers["Location"] = f"{request.url.path}/{info['documentId']}"
    return info


@controller.get("/{documentId}")
def get_document(applicationId: str, documentId: str, claims: dict = Permission):
    return download(*document_service.document(application_service.own(claims["sub"], applicationId), documentId))


@controller.delete("/{documentId}", status_code=204)
def delete_document(applicationId: str, documentId: str, claims: dict = Permission):
    document_service.delete_document(applicationId, documentId, claims["sub"])

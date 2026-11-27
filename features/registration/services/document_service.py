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
"""Supporting documents of an application (README 7.7 to 7.9, 7.14): upload, download, delete.

The metadata is part of the application (`documents`), the bytes are kept by the repository apart from it.
"""
from __future__ import annotations

import hashlib
import re
import uuid

from features.registration.managers import application_repository, config
from features.registration.managers.application_repository import applications_lock
from features.registration.models import errors as problems
from features.registration.models.applications import DocumentInfo
from features.registration.models.tables import ApplicationRow
from features.registration.models.value_sets import ApplicationStatus, DocumentType, Verification
from features.registration.services.application_service import any_application, own, require_created
from features.registration.services.shared import (
    as_json,
    audit_entry,
    field_error,
    utc_now,
    validation_problem,
)

DOCUMENT_TYPES = tuple(DocumentType)
SIGNATURES = ((b"%PDF-", "application/pdf"), (b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


def document_max_bytes() -> int:
    """The controller reads at most this plus one byte of an upload."""
    return config.document_max_bytes()


def _file_errors(document_type: str, file_name: str | None, content: bytes) -> tuple[list[dict], str | None]:
    """7.7: type, name, format by the first bytes and size; returns the errors and the content type."""
    errors: list[dict] = []
    if document_type not in DOCUMENT_TYPES:
        errors.append(field_error("documentType", f"one of {', '.join(DOCUMENT_TYPES)}"))
    if not file_name or len(file_name) > 200 or re.search(r"[/\\\x00-\x1f]", file_name):
        errors.append(field_error("file", "file name of 1 to 200 characters, without path parts and control "
                                          "characters"))
    content_type = next((t for magic, t in SIGNATURES if content.startswith(magic)), None)
    if content_type is None:
        errors.append(field_error("file", "PDF, PNG or JPEG, checked by the first bytes"))
    maximum = config.document_max_bytes()
    if not 1 <= len(content) <= maximum:
        errors.append(field_error("file", f"1 to {maximum} bytes"))
    return errors, content_type


def upload_document(application_id: str, sub: str, document_type: str, file_name: str | None,
                    content: bytes) -> DocumentInfo:
    """7.7."""
    a = own(sub, application_id)
    if a.status != ApplicationStatus.CREATED or a.verification == Verification.EBW:
        raise problems.invalid_state("only in status CREATED and the verification path DOCUMENTS")
    errors, content_type = _file_errors(document_type, file_name, content)
    with applications_lock:
        a = own(sub, application_id)
        require_created(a)
        if len(a.documents) >= config.document_max_count():
            errors.append(field_error("file", "too many supporting documents"))
        if errors:
            raise validation_problem(errors)
        info = DocumentInfo(document_id=str(uuid.uuid4()), document_type=document_type, file_name=file_name or "",
                            content_type=content_type or "", size_bytes=len(content),
                            sha256=hashlib.sha256(content).hexdigest(), uploaded_at=utc_now())
        a.documents = [*a.documents, as_json(info)]
        a.changed_at = utc_now()
        application_repository.add_document(a, info.document_id, content,
                                            audit_entry(a, "uploadDocument", sub=sub, object_id=info.document_id))
        return info


def document(a: ApplicationRow, document_id: str) -> tuple[dict, bytes]:
    """The metadata (`DocumentInfo` JSON) and the bytes of a document of this application."""
    info = next((d for d in a.documents if d["documentId"] == document_id), None)
    content = application_repository.document_content(document_id) if info else None
    if info is None or content is None:
        raise problems.not_found()
    return info, content


def own_document(sub: str, application_id: str, document_id: str) -> tuple[dict, bytes]:
    """7.8, scope `own`."""
    return document(own(sub, application_id), document_id)


def staff_document(application_id: str, document_id: str, sub: str) -> tuple[dict, bytes]:
    """7.14: every retrieval is in the audit log."""
    a = any_application(application_id)
    found = document(a, document_id)
    application_repository.audit(audit_entry(a, "getAnyDocument", sub=sub, object_id=document_id))
    return found


def delete_document(application_id: str, document_id: str, sub: str) -> None:
    """7.9."""
    with applications_lock:
        a = own(sub, application_id)
        require_created(a)
        document(a, document_id)
        a.documents = [d for d in a.documents if d["documentId"] != document_id]
        a.changed_at = utc_now()
        application_repository.delete_document(a, document_id,
                                               audit_entry(a, "deleteDocument", sub=sub, object_id=document_id))

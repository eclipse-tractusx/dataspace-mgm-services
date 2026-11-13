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
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid

from features.registration.managers.application_repository import applications_lock
from features.registration.services.application_service import any_application, own
from features.registration.services.shared import MODULE, field_error, utc_now, validation_problem, write_audit
from portal_common.problems import Problem

DOCUMENT_TYPES = ("COMMERCIAL_REGISTER_EXTRACT", "POWER_OF_ATTORNEY", "OTHER")
SIGNATURES = ((b"%PDF-", "application/pdf"), (b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


# --------------------------------------------------------------------- supporting documents (7.7 to 7.9)
def document_max_bytes() -> int:
    return int(os.environ.get("DOCUMENT_MAX_BYTES") or 10485760)


def upload_document(application_id: str, sub: str, document_type: str, file_name: str | None, content: bytes) -> dict:
    a = own(sub, application_id)
    if a["status"] != "CREATED" or a["verification"] == "EBW":
        raise Problem(MODULE, 409, "invalid-state", detail="only in status CREATED and the verification path DOCUMENTS")
    errors: list[dict] = []
    if document_type not in DOCUMENT_TYPES:
        errors.append(field_error("documentType", f"one of {', '.join(DOCUMENT_TYPES)}"))
    if not file_name or len(file_name) > 200 or re.search(r"[/\\\x00-\x1f]", file_name):
        errors.append(field_error("file", "file name of 1 to 200 characters, without path parts and control characters"))
    content_type = next((t for magic, t in SIGNATURES if content.startswith(magic)), None)
    if content_type is None:
        errors.append(field_error("file", "PDF, PNG or JPEG, checked by the first bytes"))
    maximum = document_max_bytes()
    if not 1 <= len(content) <= maximum:
        errors.append(field_error("file", f"1 to {maximum} bytes"))
    with applications_lock:
        if a["status"] != "CREATED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        if len(a["documents"]) >= int(os.environ.get("DOCUMENT_MAX_COUNT") or 10):
            errors.append(field_error("file", "too many supporting documents"))
        if errors:
            raise validation_problem(errors)
        info = {"documentId": str(uuid.uuid4()), "documentType": document_type, "fileName": file_name,
                "contentType": content_type, "sizeBytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                "uploadedAt": utc_now()}
        a["documents"].append(info)
        a["_files"][info["documentId"]] = content
        a["changedAt"] = utc_now()
        write_audit(a, "uploadDocument", sub=sub, object_id=info["documentId"])
        return info


def document(a: dict, document_id: str) -> tuple[dict, bytes]:
    info = next((d for d in a["documents"] if d["documentId"] == document_id), None)
    if info is None:
        raise Problem(MODULE, 404, "not-found")
    return info, a["_files"][document_id]


def staff_document(application_id: str, document_id: str, sub: str) -> tuple[dict, bytes]:
    """7.14: every retrieval is in the audit log."""
    a = any_application(application_id)
    found = document(a, document_id)
    with applications_lock:
        write_audit(a, "getAnyDocument", sub=sub, object_id=document_id)
    return found


def delete_document(application_id: str, document_id: str, sub: str) -> None:
    a = own(sub, application_id)
    with applications_lock:
        if a["status"] != "CREATED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        document(a, document_id)
        a["documents"] = [d for d in a["documents"] if d["documentId"] != document_id]
        a["_files"].pop(document_id, None)
        a["changedAt"] = utc_now()
        write_audit(a, "deleteDocument", sub=sub, object_id=document_id)

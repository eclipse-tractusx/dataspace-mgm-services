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
"""Helpers every registration service uses: the spec id, the clock, the audit entry, validation Problems.
"""
from __future__ import annotations

import datetime as dt

from features.registration.managers.application_repository import audit_log
from features.registration.services import attestation_verifier
from portal_common.problems import Problem

MODULE = "c1-m2"
ATTESTATION_MAX_CHARS = 16384


def utc_now() -> str:
    return dt.datetime.fromtimestamp(attestation_verifier.now(), dt.UTC).isoformat()


def write_audit(a: dict, operation: str, sub: str | None = None, step: dict | None = None, object_id: str | None = None) -> None:
    audit_log.append({"at": utc_now(), "sub": sub, "processId": (step or {}).get("processId"),
                      "stepRunId": (step or {}).get("stepRunId"), "companyId": a["companyId"], "operation": operation,
                      "applicationId": a["id"], "objectId": object_id})


def validation_problem(errors: list[dict], **ext) -> Problem:
    return Problem(MODULE, 400, "validation", errors=errors, **ext)


def field_error(field: str, message: str) -> dict:
    return {"field": field, "message": message}


def paginate(items: list[dict], page: int, size: int) -> dict:
    return {"items": items[page * size:(page + 1) * size], "page": page, "size": size, "total": len(items)}

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
"""What Process Orchestration and other services call: the steps `complete-application` and
`close-application` (README 8) and the queries 9.1 to 9.3.
"""
from __future__ import annotations

from features.registration.managers import reference_catalog
from features.registration.managers.application_repository import applications, applications_lock
from features.registration.services import attestation_verifier
from features.registration.services.application_views import public, summary
from features.registration.services.shared import MODULE, field_error, utc_now, write_audit
from portal_common import events
from portal_common.problems import Problem


# --------------------------------------------------------------------------------- steps (README 8)
def _step_application(input: dict) -> dict:
    a = applications.get(input.get("applicationId"))
    if not a:
        raise Problem(MODULE, 404, "not-found", retryable=False)
    return a


def _step_result(input: dict, a: dict) -> dict:
    return {"stepRunId": input.get("stepRunId"), "state": "DONE",
            "result": {"applicationId": a["id"], "companyId": a["companyId"], "kind": a["kind"], "status": a["status"]}}


def complete_application(input: dict) -> dict:
    with applications_lock:
        a = _step_application(input)
        if a["status"] == "SUBMITTED":
            now = utc_now()
            a.update(status="COMPLETED", completedAt=now, changedAt=now)
            events.publish(MODULE, "ApplicationCompleted", {"applicationId": a["id"], "companyId": a["companyId"], "kind": a["kind"]})
        elif a["status"] != "COMPLETED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}", retryable=False)
        write_audit(a, "stepCompleteApplication", step=input)
        return _step_result(input, a)


def close_application(input: dict) -> dict:
    reason = input.get("reason")
    if not (isinstance(reason, str) and 1 <= len(reason) <= 1000):
        raise Problem(MODULE, 400, "validation", errors=[field_error("reason", "1 to 1000 characters")], retryable=False)
    with applications_lock:
        a = _step_application(input)
        if a["status"] == "SUBMITTED":
            now = utc_now()
            a.update(status="DECLINED", declineReason=reason, closedAt=now, changedAt=now)
        elif a["status"] not in ("DECLINED", "WITHDRAWN"):
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}", retryable=False)
        write_audit(a, "stepCloseApplication", step=input)
        return _step_result(input, a)


# ------------------------------------------------------------------------------- queries (README 9)
def get_application_internal(*, applicationId: str, **_other) -> dict:
    a = applications.get(applicationId)
    if not a:
        raise Problem(MODULE, 404, "not-found")
    detail = None
    if a.get("_attestation"):
        detail = a["_attestation"] | {"signatureCheck": attestation_verifier.signature_check(a["_raw"])}
    return public(a) | {"attestation": detail, "requiredAgreements": a["_requiredAgreements"]}


def list_applications_internal(*, applicationId: list[str] | str | None = None, **_other) -> list[dict]:
    """`ApplicationSummary` in the order of the request; unknown IDs are left out."""
    ids = [applicationId] if isinstance(applicationId, str) else applicationId or []
    return [summary(a) for i in ids if (a := applications.get(i))]


def list_agreements_internal(*, status: str | None = None, **_other) -> list[dict]:
    wanted = status or "ACTIVE"
    return [a for a in reference_catalog.versions() if a["status"] == wanted]

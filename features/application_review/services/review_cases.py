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
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""Review cases of C1-M3 Application Review: the steps `open-review` and `close-review`, the query
`getReviewStatusByApplication`, and the decisions of OSP staff (README 7, 8, 9).

A case is a `ReviewCaseRow` of `managers/review_case_repository.py`; every change happens while holding the
repository's lock, which stands for the row lock of 6.8. The functions return the API models of `models/`.
"""
from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Sequence

from portal_common import events
from portal_common.models import StepResult

from ..managers import neighbour_client
from ..managers import review_case_repository as repository
from ..managers.config import config
from ..models.errors import problem
from ..models.requests import CloseReviewStep, OpenReviewStep
from ..models.review_case import (
    ApplicationBrief,
    CheckCounts,
    CheckOutcome,
    CloseReviewResult,
    OpenReviewResult,
    ReviewCase,
    ReviewCasePage,
    ReviewCaseSummary,
    ReviewStatusInfo,
)
from ..models.tables import AuditLogRow, ReviewCaseRow
from ..models.validation import parse
from ..models.value_sets import CHECK_ORDER, IN_REVIEW, MODULE, Status
from . import checks

_COUNTS = {"passed": "PASSED", "failed": "FAILED", "not_applicable": "NOT_APPLICABLE", "error": "ERROR"}


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def required_checks(case: ReviewCaseRow, cfg: dict) -> list[str]:
    """Enabled checks, plus `CSP_MATCH_EXPECTED` for `TRANSFER` and `REACTIVATION` (6.2), in the order of 6.2."""
    want = set(cfg["enabled"]) | ({"CSP_MATCH_EXPECTED"} if case.kind in ("TRANSFER", "REACTIVATION") else set())
    return [k for k in CHECK_ORDER if k in want]


def _result(case: ReviewCaseRow, key: str) -> str | None:
    return (case.checks.get(key) or {}).get("result")


def _audit(case: ReviewCaseRow, operation: str, sub: str | None = None,
           step: OpenReviewStep | CloseReviewStep | None = None) -> None:
    repository.audit(AuditLogRow(at=_now(), sub=sub, process_id=step.process_id if step else None,
                                 step_run_id=step.step_run_id if step else None, company_id=case.company_id,
                                 operation=operation, review_case_id=case.id, application_id=case.application_id))


def _event_fields(case: ReviewCaseRow) -> dict:
    return {"applicationId": case.application_id, "companyId": case.company_id, "kind": case.kind,
            "existingCompany": case.existing_company}


def _approved(case: ReviewCaseRow, sub: str | None, comment: str | None, auto: bool = False) -> None:
    now = _now()
    case.status, case.changed_at = Status.APPROVED, now
    case.decision = {"decidedAt": now, "comment": comment, "decidedBy": sub, "autoApproved": auto}
    data = _event_fields(case)
    if case.kind in ("TRANSFER", "REACTIVATION"):
        data["bpn"] = case.csp_bpn
    events.publish(MODULE, "ApplicationApproved", data)


def _ordered_checks(case: ReviewCaseRow) -> list[dict]:
    return [case.checks[k] for k in CHECK_ORDER if k in case.checks]


def view(case: ReviewCaseRow, application: dict | None = None) -> ReviewCase:
    """`ReviewCase` (openapi); `application` only for `GET /review-cases/{id}`."""
    data = case.model_dump(exclude={"seq", "rejected", "changed_at"}) | {"checks": _ordered_checks(case)}
    if application is not None:
        data["application"] = application
    return ReviewCase.model_validate(data)


def _new_case(app: dict, status: Status) -> ReviewCaseRow:
    now = _now()
    return ReviewCaseRow(
        id=str(uuid.uuid4()), application_id=app["id"], company_id=app["companyId"], kind=app["kind"],
        existing_company=bool(app.get("existingCompany")), verification=app["verification"],
        applicant_sub=(app.get("applicant") or {}).get("sub"), status=status, opened_at=now,
        seq=repository.next_seq(), changed_at=now,
        closure={"closedAt": now, "reason": "WITHDRAWN"} if status == Status.CLOSED else None)


def _application(application_id: str) -> dict:
    app = neighbour_client.get_application(application_id)
    if app is None:
        raise problem(404, "not-found", detail="application unknown", retryable=False)
    return app


def _four_eyes(case: ReviewCaseRow, cfg: dict) -> list[str]:
    reasons = []
    if "CHECK_FAILED" in cfg["fourEyes"] and any(c["result"] == "FAILED" for c in case.checks.values()):
        reasons.append("CHECK_FAILED")
    if "DOCUMENTS" in cfg["fourEyes"] and case.verification == "DOCUMENTS":
        reasons.append("DOCUMENTS")
    if "ALWAYS" in cfg["fourEyes"]:
        reasons.append("ALWAYS")
    return reasons


def _auto_approve(case: ReviewCaseRow, cfg: dict) -> bool:
    """6.6: kind in AUTO_APPROVE_KINDS, path EBW, every check PASSED, no four-eyes case."""
    return (case.kind in cfg["auto"] and case.verification == "EBW"
            and all(_result(case, k) == "PASSED" for k in required_checks(case, cfg))
            and not _four_eyes(case, cfg))


# ------------------------------------------------------------------------------- steps (README 8)
def _run_checks(case: ReviewCaseRow, app: dict, cfg: dict) -> None:
    """Runs every required check that has no result yet or ended with `ERROR` (8.1, idempotent)."""
    found, rejected = dict(case.checks), set(case.rejected)
    for key in required_checks(case, cfg):
        old = found.get(key)
        if old and old["result"] != "ERROR":
            continue
        result, details = checks.run(key, app)
        if details.pop(checks.REJECTED, False):
            rejected.add(key)
        else:
            rejected.discard(key)
        found[key] = {"checkKey": key, "result": result, "details": details, "checkedAt": _now(),
                      "attempts": (old or {}).get("attempts", 0) + 1}
        if key == "CSP_MATCH_EXPECTED":
            case.csp_bpn = next((m["bpn"] for m in details.get("cspMatches", []) if m["expected"]), None)
    case.checks, case.rejected, case.changed_at = found, sorted(rejected), _now()


def open_review(input: dict | OpenReviewStep) -> StepResult[OpenReviewResult]:
    step, cfg = parse(OpenReviewStep, input), config()
    aid, errors = step.application_id, []
    with repository.lock:
        case = repository.by_application(aid)
        if case is None or case.status == "OPEN":
            app = _application(aid)
            if case is None:
                if app["status"] == "SUBMITTED":
                    case = _new_case(app, Status.OPEN)
                elif app["status"] == "WITHDRAWN":
                    case = _new_case(app, Status.CLOSED)
                else:
                    raise problem(409, "invalid-state", detail=f"application is {app['status']}",
                                  retryable=False)
            if case.status == "OPEN":
                _run_checks(case, app, cfg)
                errors = [k for k, c in case.checks.items() if c["result"] == "ERROR"]
                if not errors and _auto_approve(case, cfg):
                    _approved(case, None, None, auto=True)
            case = repository.save(case)
        _audit(case, "open-review", step=step)
        if errors and set(errors) <= set(case.rejected):   # a repetition does not help (OPEN-QUESTIONS 11)
            raise problem(502, "neighbour-rejected", detail=f"checks with ERROR: {', '.join(errors)}",
                          pendingChecks=errors, retryable=False)
        if errors:
            raise problem(502, "upstream-error", detail=f"checks with ERROR: {', '.join(errors)}",
                          pendingChecks=errors, retryable=True)
        outcomes = [CheckOutcome.model_validate(c) for c in _ordered_checks(case)]
        return StepResult[OpenReviewResult].done(step, OpenReviewResult(
            review_case_id=case.id, application_id=aid, status=case.status, checks=outcomes))


def close_review(input: dict | CloseReviewStep) -> StepResult[CloseReviewResult]:
    step = parse(CloseReviewStep, input)
    aid = step.application_id
    with repository.lock:
        case = repository.by_application(aid)
        if case is None:
            app = _application(aid)
            if app["status"] != "WITHDRAWN":
                raise problem(409, "invalid-state", detail=f"application is {app['status']}", retryable=False)
            case = repository.save(_new_case(app, Status.CLOSED))
        elif case.status == "APPROVED":
            raise problem(409, "invalid-state", detail="review case already approved", retryable=False)
        elif case.status in IN_REVIEW:
            now = _now()
            case.status, case.changed_at, case.closure = Status.CLOSED, now, {"closedAt": now, "reason": step.reason}
            case = repository.save(case)
        _audit(case, "close-review", step=step)
        return StepResult[CloseReviewResult].done(step, CloseReviewResult(
            review_case_id=case.id, application_id=aid, status=case.status))


# ------------------------------------------------------------------------------ query (README 9)
def get_review_status_by_application(*, applicationId: str, **_other: object) -> ReviewStatusInfo:
    case = repository.by_application(applicationId)
    if case is None:
        raise problem(404, "not-found")
    return ReviewStatusInfo(review_case_id=case.id, application_id=applicationId, status=case.status,
                            decided_at=(case.decision or {}).get("decidedAt"))


# ------------------------------------------------------------------ operations of staff (README 7)
def _case(case_id: str) -> ReviewCaseRow:
    case = repository.get(case_id)
    if case is None:
        raise problem(404, "not-found")
    return case


def _summary(case: ReviewCaseRow, application: dict | None) -> ReviewCaseSummary:
    counts = {name: sum(c["result"] == result for c in case.checks.values()) for name, result in _COUNTS.items()}
    summary = ReviewCaseSummary(
        id=case.id, application_id=case.application_id, company_id=case.company_id, kind=case.kind,
        verification=case.verification, status=case.status, opened_at=case.opened_at,
        decided_at=(case.decision or {}).get("decidedAt"), check_counts=CheckCounts(**counts))
    if application:
        summary.application = ApplicationBrief.model_validate(application)
    return summary


def list_cases(status: Sequence[str] | None, kind: Sequence[str] | None, verification: Sequence[str] | None,
               application_id: str | None, page: int, size: int) -> ReviewCasePage:
    """7.1: one page of cases, with one call to C1-M2 for the summaries of the whole page."""
    rows, total = repository.find(status or IN_REVIEW, kind, verification, application_id, page, size)
    apps = {a["id"]: a for a in neighbour_client.list_applications([c.application_id for c in rows])}
    return ReviewCasePage(items=[_summary(c, apps.get(c.application_id)) for c in rows], page=page, size=size,
                          total=total)


def get_case(case_id: str) -> ReviewCase:
    case = _case(case_id)
    return view(case, neighbour_client.get_application(case.application_id) or {})


def _decision_allowed(case: ReviewCaseRow) -> None:
    if neighbour_client.application_status(case.application_id) == "WITHDRAWN":
        raise problem(409, "application-withdrawn")


def approve(case_id: str, sub: str, comment: str | None) -> ReviewCase:
    """7.3, in the order of the README."""
    case, cfg = _case(case_id), config()
    _decision_allowed(case)
    with repository.lock:
        case = _case(case_id)   # read again under the lock (6.8)
        if case.status == "APPROVED":
            return view(case)
        if case.status not in IN_REVIEW:
            raise problem(409, "invalid-state", detail=f"review case is {case.status}")
        if sub == case.applicant_sub:
            raise problem(403, "own-application")
        if case.status == "AWAITING_SECOND_APPROVAL" and sub == (case.first_approval or {}).get("approvedBy"):
            return view(case)
        pending = [k for k in required_checks(case, cfg) if _result(case, k) in (None, "ERROR")]
        if pending:
            raise problem(409, "checks-incomplete", pendingChecks=pending)
        csp = case.checks.get("CSP_MATCH_EXPECTED", {})
        if case.kind in ("TRANSFER", "REACTIVATION") and csp.get("result") != "PASSED":
            raise problem(409, "csp-match-required", cspOutcome=(csp.get("details") or {}).get("cspOutcome"))
        failed = [k for k in CHECK_ORDER if _result(case, k) == "FAILED"]
        if case.status == "OPEN" and failed and not comment:
            raise problem(400, "comment-required", failedChecks=failed)
        reasons = _four_eyes(case, cfg)
        if case.status == "OPEN" and reasons:
            now = _now()
            case.status, case.changed_at = Status.AWAITING_SECOND_APPROVAL, now
            case.first_approval = {"approvedBy": sub, "approvedAt": now, "comment": comment, "fourEyesReasons": reasons}
            events.publish(MODULE, "ApplicationAwaitingSecondApproval",
                           {**_event_fields(case), "reviewCaseId": case.id, "firstApproval": case.first_approval})
        else:
            _approved(case, sub, comment)
        case = repository.save(case)
        _audit(case, "approve", sub=sub)
        return view(case)


def decline(case_id: str, sub: str, reason: str) -> ReviewCase:
    """7.4, in the order of the README."""
    _decision_allowed(_case(case_id))
    with repository.lock:
        case = _case(case_id)   # read again under the lock (6.8)
        if case.status == "DECLINED":
            return view(case)
        if case.status not in IN_REVIEW:
            raise problem(409, "invalid-state", detail=f"review case is {case.status}")
        if sub == case.applicant_sub:
            raise problem(403, "own-application")
        now = _now()
        case.status, case.changed_at = Status.DECLINED, now
        case.decision = {"decidedAt": now, "comment": reason, "decidedBy": sub, "autoApproved": False}
        events.publish(MODULE, "ApplicationDeclined", {**_event_fields(case), "reason": reason})
        case = repository.save(case)
        _audit(case, "decline", sub=sub)
        return view(case)

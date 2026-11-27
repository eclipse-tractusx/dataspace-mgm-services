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

from features.registration.managers import agreement_repository, application_repository
from features.registration.managers.application_repository import applications_lock
from features.registration.models import errors as problems
from features.registration.models.applications import ApplicationInternal, ApplicationSummary
from features.registration.models.reference_data import AgreementVersion
from features.registration.models.steps import ApplicationStep, ApplicationStepResult, CloseApplicationStep
from features.registration.models.tables import ApplicationRow
from features.registration.models.value_sets import AgreementStatus, ApplicationStatus
from features.registration.services.agreement_service import version_view
from features.registration.services.application_views import internal, summary
from features.registration.services.shared import MODULE, audit_entry, field_error, parse, utc_now
from portal_common import events
from portal_common.models import StepResult
from portal_common.problems import Problem

StepAnswer = StepResult[ApplicationStepResult]


# --------------------------------------------------------------------------------- steps (README 8)
def _step_application(step: ApplicationStep) -> ApplicationRow:
    a = application_repository.get(step.application_id)
    if not a:
        raise problems.not_found(retryable=False)
    return a


def _step_result(step: ApplicationStep, a: ApplicationRow) -> StepAnswer:
    result = ApplicationStepResult(application_id=a.id, company_id=a.company_id, kind=a.kind, status=a.status)
    return StepAnswer(step_run_id=step.step_run_id, state="DONE", result=result)


def _invalid_state(a: ApplicationRow) -> Problem:
    return problems.invalid_state(f"application is {a.status}", retryable=False)


def complete_application(input: dict) -> StepAnswer:
    """The company is active: SUBMITTED becomes COMPLETED; a repetition answers DONE again."""
    step = parse(ApplicationStep, input)
    with applications_lock:
        a = _step_application(step)
        completed = a.status == ApplicationStatus.SUBMITTED
        if completed:
            now = utc_now()
            a.status, a.completed_at, a.changed_at = ApplicationStatus.COMPLETED, now, now
        elif a.status != ApplicationStatus.COMPLETED:
            raise _invalid_state(a)
        application_repository.save(a, audit=audit_entry(a, "stepCompleteApplication", step=step))
        if completed:
            events.publish(MODULE, "ApplicationCompleted", {"applicationId": a.id, "companyId": a.company_id,
                                                            "kind": a.kind})
        return _step_result(step, a)


def close_application(input: dict) -> StepAnswer:
    """The review declined: SUBMITTED becomes DECLINED; DECLINED and WITHDRAWN stay as they are."""
    reason = input.get("reason")
    if not (isinstance(reason, str) and 1 <= len(reason) <= 1000):
        raise problems.validation_problem([field_error("reason", "1 to 1000 characters")], retryable=False)
    step = parse(CloseApplicationStep, input)
    with applications_lock:
        a = _step_application(step)
        if a.status == ApplicationStatus.SUBMITTED:
            now = utc_now()
            a.status, a.decline_reason, a.closed_at, a.changed_at = ApplicationStatus.DECLINED, step.reason, now, now
        elif a.status not in (ApplicationStatus.DECLINED, ApplicationStatus.WITHDRAWN):
            raise _invalid_state(a)
        application_repository.save(a, audit=audit_entry(a, "stepCloseApplication", step=step))
        return _step_result(step, a)


# ------------------------------------------------------------------------------- queries (README 9)
def get_application_internal(*, applicationId: str, **_other: object) -> ApplicationInternal:
    a = application_repository.get(applicationId)
    if not a:
        raise problems.not_found()
    return internal(a)


def list_applications_internal(*, applicationId: list[str] | str | None = None,
                               **_other: object) -> list[ApplicationSummary]:
    """`ApplicationSummary` in the order of the request, read in one query; unknown IDs are left out."""
    ids = [applicationId] if isinstance(applicationId, str) else applicationId or []
    found = application_repository.get_many(ids)
    return [summary(found[i]) for i in ids if i in found]


def list_agreements_internal(*, status: str | None = None, **_other: object) -> list[AgreementVersion]:
    return [version_view(a) for a in agreement_repository.versions(status or AgreementStatus.ACTIVE)]

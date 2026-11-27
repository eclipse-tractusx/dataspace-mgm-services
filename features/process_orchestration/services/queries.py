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
"""The operations of the API (README 7, 9): processes, step runs, retrigger and flows, answered as models."""
from __future__ import annotations

from features.process_orchestration.models.errors import problem
from features.process_orchestration.models.process import (
    Flow,
    FlowList,
    Process,
    ProcessSummary,
    ProcessSummaryPage,
    RetriggerRequest,
    StepRun,
    StepRunDetail,
)
from features.process_orchestration.models.states import STATUSES, SUBJECT_TYPES
from features.process_orchestration.services import engine, projections


def process_dict(process_id: str) -> dict:
    """The engine's process, or 404."""
    proc = engine.get_engine().store.get(process_id)
    if not proc:
        raise problem(404, "not-found", detail="process unknown")
    return proc


def _step_dict(proc: dict, step_key: str) -> dict:
    sr = next((s for s in proc["steps"] if s["stepKey"] == step_key), None)
    if not sr:
        raise problem(404, "not-found", detail="step unknown")
    return sr


def list_processes(*, flowKey: str | None, status: str | None, subjectType: str | None, subjectId: str | None,
                   updatedSince: str | None, page: int, size: int) -> ProcessSummaryPage:
    """README 7.1: the processes, newest change first, filtered and paged."""
    if page < 0 or not 1 <= size <= 100 or (status and status not in STATUSES) or \
            (subjectType and subjectType not in SUBJECT_TYPES):
        raise problem(400, "validation")
    items = [projections.summary(p) for p in engine.get_engine().store.all()
             if (not flowKey or p["flowKey"] == flowKey) and (not status or p["status"] == status)
             and (not subjectType or p["subjectType"] == subjectType) and (not subjectId or p["subjectId"] == subjectId)
             and (not updatedSince or (projections.iso(p["updatedAt"]) or "") >= updatedSince)]
    items.sort(key=lambda x: x.updated_at, reverse=True)
    return ProcessSummaryPage.of(items, page, size)


def get_process(process_id: str) -> Process:
    return projections.process(process_dict(process_id))


def get_step_run(process_id: str, step_key: str) -> StepRunDetail:
    return projections.step_run_detail(_step_dict(process_dict(process_id), step_key))


def retrigger_step(process_id: str, step_key: str, sub: str, body: dict | None) -> StepRun:
    """README 7.4: a FAILED step runs again; 409 for any other state."""
    request = RetriggerRequest.of_body(body)
    proc = process_dict(process_id)
    _step_dict(proc, step_key)
    sr = engine.get_engine().retrigger(proc, step_key, sub, request.comment)
    if sr is None:
        raise problem(409, "invalid-state", detail="step is not FAILED")
    return projections.step_run(sr)


def list_flows() -> FlowList:
    e = engine.get_engine()
    return FlowList(items=[Flow.model_validate(f | {"version": e.version}) for f in e.flows.values()])


def get_flow(flow_key: str) -> Flow:
    e = engine.get_engine()
    fl = e.flows.get(flow_key)
    if not fl:
        raise problem(404, "not-found", detail="flow unknown")
    return Flow.model_validate(fl | {"version": e.version})


def find_processes_of_subject(*, subjectType: str, subjectId: str) -> list[ProcessSummary]:
    """`GET /internal/processes`: the processes of one subject, newest first."""
    if subjectType not in SUBJECT_TYPES:
        raise problem(400, "validation", detail="subjectType")
    items = [projections.summary(p) for p in engine.get_engine().store.of_subject(subjectType, subjectId)]
    return sorted(items, key=lambda x: x.created_at, reverse=True)

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
"""Views of a process for the API, the live stream and other modules (README 7.1 to 7.8, 9), as the models of
`models/process.py`. The engine's process dict holds datetimes; the views carry them as ISO strings."""
from __future__ import annotations

import datetime as dt

from features.process_orchestration.models.process import (
    Process,
    ProcessChanged,
    ProcessSummary,
    StepRun,
    StepRunDetail,
)
from features.process_orchestration.models.states import FINAL_STEP


def iso(t: dt.datetime | None) -> str | None:
    return t.isoformat() if t else None


def current_step(p: dict) -> str | None:
    """The first step that is not DONE or SKIPPED."""
    return next((s["stepKey"] for s in p["steps"] if s["state"] not in FINAL_STEP), None)


def _summary_fields(p: dict) -> dict:
    return {"id": p["id"], "flowKey": p["flowKey"], "flowVersion": p["flowVersion"], "subjectType": p["subjectType"],
            "subjectId": p["subjectId"], "status": p["status"], "currentStep": current_step(p),
            "endReason": p["endReason"], "createdAt": iso(p["createdAt"]), "updatedAt": iso(p["updatedAt"]),
            "finishedAt": iso(p["finishedAt"])}


def summary(p: dict) -> ProcessSummary:
    """Process summary of README 7.1 and 9."""
    return ProcessSummary.model_validate(_summary_fields(p))


def _step_fields(s: dict) -> dict:
    return {"stepRunId": s["stepRunId"], "stepKey": s["stepKey"], "call": s["call"], "state": s["state"],
            "attempts": s["attempts"], "maxAttempts": s["maxAttempts"], "lastError": s["lastError"],
            "nextAttemptAt": iso(s["nextAttemptAt"]), "awaitUntil": iso(s["awaitUntil"]),
            "startedAt": iso(s["startedAt"]), "finishedAt": iso(s["finishedAt"])}


def step_run(s: dict) -> StepRun:
    """A step run of README 7.2."""
    return StepRun.model_validate(_step_fields(s))


def step_run_detail(s: dict) -> StepRunDetail:
    """README 7.3: a step run with its result and attempts."""
    return StepRunDetail.model_validate(_step_fields(s) | {"result": s["result"], "attempts_": s["attemptHistory"]})


def process(p: dict) -> Process:
    """README 7.2: a process with its variables and step runs."""
    return Process.model_validate(_summary_fields(p) | {"variables": p["variables"],
                                                       "steps": [_step_fields(s) for s in p["steps"]]})


def process_changed(p: dict) -> ProcessChanged:
    """`data` of the stream event `process-changed` (README 7.6, `ProcessChanged`): IDs, keys and
    states only; no variables, results or errors."""
    return ProcessChanged.model_validate(
        {"processId": p["id"], "flowKey": p["flowKey"], "subjectType": p["subjectType"],
         "subjectId": p["subjectId"], "status": p["status"], "currentStep": current_step(p),
         "endReason": p["endReason"], "steps": [{"stepKey": r["stepKey"], "state": r["state"]} for r in p["steps"]],
         "updatedAt": iso(p["updatedAt"])})


def stream_meta(p: dict) -> dict:
    """Who may see the stream events of a process (README 7.7, 7.8); never sent to the UI."""
    return {"processId": p["id"], "subjectType": p["subjectType"], "subjectId": p["subjectId"],
            "applicantSub": p["variables"].get("applicantSub")}

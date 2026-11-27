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
"""The API models of Process Orchestration (openapi.yaml `components.schemas`), built on `portal_common.models`.

The engine keeps a process as a plain dict (it is mutated step by step under the engine lock); these models are the
views of it that leave the feature: responses of the API, the stream event `process-changed` and the query of
other modules. Timestamps are already ISO strings when a model is built.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field, ValidationError

from features.process_orchestration.models.errors import problem
from features.process_orchestration.models.states import ProcessStatus, StepState, SubjectType
from portal_common.models import ApiModel, Page


class ProcessSummary(ApiModel):
    """A process in lists (README 7.1, 9). `subjectId` stays a plain string: a flow takes it from an event."""

    id: str
    flow_key: str
    flow_version: int | None = None
    subject_type: SubjectType
    subject_id: str | None = None
    status: ProcessStatus
    current_step: str | None = None
    end_reason: str | None = None
    created_at: str
    updated_at: str
    finished_at: str | None = None


ProcessSummaryPage = Page[ProcessSummary]


class StepError(ApiModel):
    """`lastError` of a step run; further fields of the answer (`detail`) are kept as they came."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    status: int | None = None
    title: str | None = None
    retryable: bool


class StepAttempt(ApiModel):
    number: int = Field(ge=1)
    trigger: Literal["WORKER", "RETRIGGER"]
    triggered_by: str | None = None
    started_at: str
    finished_at: str | None = None
    outcome: Literal["DONE", "RUNNING", "ERROR"] | None = None
    error_type: str | None = None


class StepRun(ApiModel):
    """A step run of one process (README 7.2)."""

    step_run_id: str
    step_key: str
    call: str
    state: StepState
    attempts: int = Field(ge=0)
    max_attempts: int = Field(ge=1)
    last_error: StepError | None = None
    next_attempt_at: str | None = None
    await_until: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class StepRunDetail(StepRun):
    """README 7.3: a step run with its result and attempts. The attempts leave as `attempts_`, as before the
    migration (openapi.yaml names them `attemptHistory`, OPEN-QUESTIONS.md 3)."""

    result: dict[str, Any] | None = None
    attempt_history: list[StepAttempt] = Field(alias="attempts_")


class Process(ProcessSummary):
    """README 7.2: a process with its variables and step runs."""

    variables: dict[str, Any]
    steps: list[StepRun]


class StepStateOfProcess(ApiModel):
    step_key: str
    state: StepState


class ProcessChanged(ApiModel):
    """`data` of the stream event `process-changed` (README 7.6): IDs, keys and states only."""

    process_id: str
    flow_key: str
    subject_type: SubjectType
    subject_id: str | None = None
    status: ProcessStatus
    current_step: str | None = None
    end_reason: str | None = None
    steps: list[StepStateOfProcess]
    updated_at: str


class RetriggerRequest(ApiModel):
    """README 7.4; further fields are ignored, as `additionalProperties` is not false in the spec."""

    comment: str | None = Field(None, max_length=500)

    @classmethod
    def of_body(cls, body: dict | None) -> RetriggerRequest:
        """The request of an optional body; a wrong `comment` is the Problem of README 12, not a 422."""
        try:
            return cls.model_validate(body or {})
        except ValidationError:
            raise problem(400, "validation", detail="comment up to 500 characters") from None


class Flow(ApiModel):
    """A flow as in flows.yaml (README 6.1, 7.5); the optional parts of a flow are passed on as they are."""

    model_config = ConfigDict(extra="allow")

    key: str
    version: int
    trigger: dict[str, Any]
    subject: dict[str, Any]
    correlate_by: str
    steps: list[dict[str, Any]]


class FlowList(ApiModel):
    items: list[Flow]

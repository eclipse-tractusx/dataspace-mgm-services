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
"""Models of the steps `complete-application` and `close-application` (README 8).

The step input stays tolerant like the other steps of the module: a missing `applicationId` is 404
`not-found` (README 8), not a validation error, and `processId`/`stepRunId` only serve the audit log.
"""
from __future__ import annotations

from pydantic import ConfigDict

from features.registration.models.value_sets import ApplicationKind, ApplicationStatus
from portal_common.models import ApiModel


class ApplicationStep(ApiModel):
    """`StepApplicationRef`; further fields of the call (Process Orchestration passes its step input) are ignored."""

    model_config = ConfigDict(extra="ignore")

    process_id: str | None = None
    step_run_id: str | None = None
    application_id: str | None = None


class CloseApplicationStep(ApplicationStep):
    """`StepCloseApplication`, after the check of `reason`."""
    reason: str


class ApplicationStepResult(ApiModel):
    """`result` of `StepResultApplication`."""
    application_id: str
    company_id: str
    kind: ApplicationKind
    status: ApplicationStatus

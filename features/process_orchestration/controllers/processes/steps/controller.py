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
"""The step runs of a process and their retrigger (README 7.3, 7.4)."""
from __future__ import annotations

from fastapi import Body

from features.process_orchestration import interface
from features.process_orchestration.models.process import StepRun, StepRunDetail
from portal_common.routing import Controller, Permission

controller = Controller("Process Orchestration: Processes")


@controller.get("/{stepKey}", response_model=StepRunDetail, summary="A step run with its result and attempts")
def get_step_run(processId: str, stepKey: str, _: dict = Permission) -> StepRunDetail:
    return interface.get_step_run(processId, stepKey)


@controller.post("/{stepKey}/retrigger", status_code=202, response_model=StepRun, summary="Run a FAILED step again")
def retrigger_step(processId: str, stepKey: str, claims: dict = Permission,
                   body: dict | None = Body(None)) -> StepRun:
    """The body is checked by the service (`RetriggerRequest`), so a wrong `comment` keeps its Problem detail."""
    return interface.retrigger_step(processId, stepKey, claims["sub"], body)

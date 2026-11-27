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
"""The processes of the installation for OSP staff (README 7.1, 7.2)."""
from __future__ import annotations

from features.process_orchestration import interface
from features.process_orchestration.models.process import Process, ProcessSummaryPage
from portal_common.routing import Controller, Permission

controller = Controller("Process Orchestration: Processes")


@controller.get("", response_model=ProcessSummaryPage, summary="List the processes")
def list_processes(flowKey: str | None = None, status: str | None = None, subjectType: str | None = None,
                   subjectId: str | None = None, updatedSince: str | None = None, page: int = 0, size: int = 20,
                   _: dict = Permission) -> ProcessSummaryPage:
    return interface.list_processes(flowKey=flowKey, status=status, subjectType=subjectType, subjectId=subjectId,
                                    updatedSince=updatedSince, page=page, size=size)


@controller.get("/{processId}", response_model=Process, summary="A process with its variables and step runs")
def get_process(processId: str, _: dict = Permission) -> Process:
    return interface.get_process(processId)

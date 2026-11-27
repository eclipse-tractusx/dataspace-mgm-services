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
"""Public interface of C12-M1 Process Orchestration (README 9) and the entry points of its controllers.

Other modules call only `find_processes_of_subject` (C12-M1 has no steps). The other functions are the
operations of the API, returned as the models of `models/process.py`; the controllers call them here.
"""
from __future__ import annotations

from features.process_orchestration.models.errors import MODULE
from features.process_orchestration.services import queries, streams
from portal_common import standin

list_processes = queries.list_processes
get_process = queries.get_process
get_step_run = queries.get_step_run
retrigger_step = queries.retrigger_step
list_flows = queries.list_flows
get_flow = queries.get_flow
processes_of_subject = queries.find_processes_of_subject
process_stream = streams.of_process
application_stream = streams.of_application


def find_processes_of_subject(*, subjectType: str, subjectId: str) -> list[dict]:
    """`GET /internal/processes`: the processes of one subject, newest first, as JSON (the same as over HTTP)."""
    return [p.model_dump(mode="json") for p in queries.find_processes_of_subject(subjectType=subjectType,
                                                                                 subjectId=subjectId)]


__getattr__ = standin.missing_interface(MODULE)

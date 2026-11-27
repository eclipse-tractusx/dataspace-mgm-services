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
"""Value sets of Process Orchestration (openapi.yaml, README 5, 6.3, 6.4): process states, step states and subject
types, and the groups of states the engine works with."""
from __future__ import annotations

from enum import StrEnum


class SubjectType(StrEnum):
    APPLICATION = "APPLICATION"
    COMPANY = "COMPANY"
    TECHNICAL_USER = "TECHNICAL_USER"
    OFFER = "OFFER"
    SUBSCRIPTION = "SUBSCRIPTION"
    CONNECTOR = "CONNECTOR"


class ProcessStatus(StrEnum):
    """README 6.4."""

    RUNNING = "RUNNING"
    WAITING = "WAITING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    ENDED = "ENDED"


class StepState(StrEnum):
    """README 6.3."""

    WAITING = "WAITING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_EVENT = "AWAITING_EVENT"
    DONE = "DONE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


STATUSES = frozenset(ProcessStatus)
SUBJECT_TYPES = frozenset(SubjectType)
OPEN = frozenset({ProcessStatus.RUNNING, ProcessStatus.WAITING, ProcessStatus.FAILED})   # a trigger joins these
FINAL_STEP = frozenset({StepState.DONE, StepState.SKIPPED})                             # the next step runs after these

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
"""Problem Details of C11-M1 (README 12): `urn:c11-m1:problem:<name>`."""
from __future__ import annotations

from features.notifications.models import MODULE
from portal_common.problems import Problem


def not_found() -> Problem:
    """404: the notification is not in the caller's own inbox (README 7)."""
    return Problem(MODULE, 404, "not-found")


def task_open() -> Problem:
    """409: an open task cannot be hidden (README 7.5)."""
    return Problem(MODULE, 409, "task-open")

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
"""Factory of the C10-M1 Problem Details (README section 12): every error of the feature is built here."""
from __future__ import annotations

from features.subscriptions.models.subscription import MODULE
from portal_common.problems import Problem


def problem(status: int, name: str, *, detail: str | None = None, retryable: bool | None = None) -> Problem:
    """`urn:c10-m1:problem:<name>`; `retryable` (steps, FRAMEWORK 4.4) is in the body only when it is given."""
    if retryable is None:
        return Problem(MODULE, status, name, detail=detail)
    return Problem(MODULE, status, name, detail=detail, retryable=retryable)


def invalid(fields: list[str]) -> Problem:
    """400 `validation` naming the invalid fields, never their values."""
    return problem(400, "validation", detail="invalid: " + ", ".join(fields), retryable=False)

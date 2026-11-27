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
"""Factory for the Problem Details of App Access (README 12); `exception_translator.py` maps the exceptions of
`models/exception/` onto it."""
from __future__ import annotations

from features.app_access.models.utils import MODULE
from portal_common.problems import Problem


def problem(status: int, name: str, *, detail: str | None = None, **extensions: object) -> Problem:
    """Problem `urn:c2-m2:problem:<name>`; the extension members (`retryable`, details) go next to `detail`."""
    result = Problem(MODULE, status, name, detail=detail)
    result.ext = dict(extensions)
    return result

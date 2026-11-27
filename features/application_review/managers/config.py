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
"""Configuration of README section 4, read from the environment at call time."""
from __future__ import annotations

import os

from ..models.value_sets import AUTO_KINDS, CHECK_ORDER, FOUR_EYES


def _list(var: str, default: str) -> list[str]:
    return [v.strip() for v in os.environ.get(var, default).split(",") if v.strip()]


def config() -> dict:
    """Configuration of README 4; invalid values raise ValueError (6.6)."""
    enabled = _list("ENABLED_CHECKS", ",".join(CHECK_ORDER))
    four_eyes = _list("FOUR_EYES_CASES", "CHECK_FAILED,DOCUMENTS")
    auto = _list("AUTO_APPROVE_KINDS", "")
    if bad := set(enabled) - set(CHECK_ORDER):
        raise ValueError(f"ENABLED_CHECKS: unknown checks {sorted(bad)}")
    if bad := set(four_eyes) - FOUR_EYES:
        raise ValueError(f"FOUR_EYES_CASES: unknown cases {sorted(bad)}")
    if bad := set(auto) - AUTO_KINDS:
        raise ValueError(f"AUTO_APPROVE_KINDS: not allowed {sorted(bad)} (REACTIVATION never, 6.6)")
    return {"enabled": enabled, "fourEyes": four_eyes, "auto": auto}


def duplicate_check_identifier_types() -> list[str]:
    """Identifier types of the duplicate check `NO_DUPLICATE` (README 4, 6.2)."""
    return _list("DUPLICATE_CHECK_IDENTIFIER_TYPES", "EUID,EBWOID,VAT_ID,LEI_CODE")


def stub_file(var: str) -> str:
    """Path of a stand-in file of a neighbour (`STUB_APPLICATIONS_FILE`, ...), empty if not set (README 14)."""
    return os.environ.get(var, "")

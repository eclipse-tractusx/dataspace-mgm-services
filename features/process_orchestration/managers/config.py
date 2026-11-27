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
"""Configuration of Process Orchestration, read from the environment at call time (AGENTS.md rule 6).

The engine reads it once when it is built (`reset()`), the worker when it starts.
"""
from __future__ import annotations

import os


def flows_check() -> str:
    """`FLOWS_CHECK`: `strict` (default) stops the start on a warning of the check, `warn` only logs it (README 6.2)."""
    return os.environ.get("FLOWS_CHECK", "strict")


def retry_base() -> float:
    return float(os.environ.get("RETRY_BASE_SECONDS", 5))


def retry_factor() -> float:
    return float(os.environ.get("RETRY_FACTOR", 2))


def retry_max() -> float:
    return float(os.environ.get("RETRY_MAX_SECONDS", 600))


def max_attempts(default: int) -> int:
    """`MAX_ATTEMPTS`, else `defaults.maxAttempts` of the flow file (passed as `default`)."""
    return int(os.environ.get("MAX_ATTEMPTS", default))


def step_timeout() -> float:
    return float(os.environ.get("STEP_TIMEOUT_SECONDS", 30))


def await_timeout() -> str | None:
    """`AWAIT_TIMEOUT` (ISO 8601 duration); a step setting wins, the flow file's default comes after it."""
    return os.environ.get("AWAIT_TIMEOUT")


def standin_file() -> str | None:
    """`STANDIN_FILE`: YAML with `steps` and `lookups` that replace the built-in stand-in answers (README 11.3)."""
    return os.environ.get("STANDIN_FILE") or None


def worker_poll_seconds() -> float:
    return float(os.environ.get("WORKER_POLL_SECONDS", 2))

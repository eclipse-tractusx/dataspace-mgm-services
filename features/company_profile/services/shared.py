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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Helpers every company profile service uses: the spec id, timestamps and the audit entry of a step.
"""
from __future__ import annotations

import datetime as dt

from features.company_profile.managers import company_repository

MODULE = "c3-m1"


def parse_timestamp(value: str | None) -> dt.datetime | None:
    """Parse a stored ISO timestamp (`Z` or offset) to an instant; `None` when unreadable."""
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def audit_step(company_id: str | None, operation: str, input: dict, details: dict | None = None) -> None:
    """Steps carry `processId` and `stepRunId` instead of a `sub` (README 5, 4.3)."""
    company_repository.audit(company_id, None, operation, None,
                (details or {}) | {"processId": input.get("processId"),
                                   "stepRunId": input.get("stepRunId")})

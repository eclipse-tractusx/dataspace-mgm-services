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
"""Helpers every registration service uses: the clock, the audit entry, paging and the JSON form of a view.
The Problem factories are in `models.errors`.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Sequence
from typing import Any

from features.registration.models import MODULE
from features.registration.models.errors import field_error, parse, validation_problem
from features.registration.models.steps import ApplicationStep
from features.registration.models.tables import ApplicationRow, AuditRow
from features.registration.services import attestation_verifier
from portal_common.models import ApiModel, Page

ATTESTATION_MAX_CHARS = 16384

__all__ = ["ATTESTATION_MAX_CHARS", "MODULE", "as_json", "audit_entry", "field_error", "page_of", "parse", "utc_now",
           "validation_problem"]


def utc_now() -> str:
    return dt.datetime.fromtimestamp(attestation_verifier.now(), dt.UTC).isoformat()


def audit_entry(a: ApplicationRow | None, operation: str, sub: str | None = None, step: ApplicationStep | None = None,
                object_id: str | None = None) -> AuditRow:
    """An entry of the audit log (README 10): no personal data beyond the `sub`."""
    return AuditRow(at=utc_now(), sub=sub, process_id=step.process_id if step else None,
                    step_run_id=step.step_run_id if step else None, company_id=a.company_id if a else None,
                    operation=operation, application_id=a.id if a else None, object_id=object_id)


def page_of[R](rows: Sequence[R], page: int, size: int, view: Callable[[R], ApiModel]) -> Page[Any]:
    """One page of rows already filtered and sorted; only the rows of the page become views."""
    window = Page.of(rows, page, size)
    return Page(items=[view(row) for row in window.items], page=window.page, size=window.size, total=window.total)


def as_json(model: ApiModel) -> dict:
    """The JSON of a view as the HTTP API sends it (`response_model_exclude_unset`): a field a stored object never had
    stays out, `null` stays where the object has it. In-process callers get the same JSON as HTTP callers."""
    return model.model_dump(mode="json", by_alias=True, exclude_unset=True)

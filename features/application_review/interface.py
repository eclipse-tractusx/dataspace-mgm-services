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
"""In-process contract of the application review (call convention, AGENTS.md): the steps `open-review` and
`close-review` of README 8, the query `getReviewStatusByApplication` of README 9, and the decisions of OSP staff
(README 7). The controllers, other modules and Process Orchestration import only from here and get the JSON form
of the answer (camelCase, as over HTTP); the logic lives in `services/`."""
from __future__ import annotations

from collections.abc import Sequence

from features.application_review import services
from features.application_review.models.requests import CloseReviewStep, OpenReviewStep
from features.application_review.models.value_sets import MODULE
from features.application_review.services import config, reset
from portal_common.models import ApiModel

__all__ = [
    "MODULE", "approve", "close_review", "config", "decline", "get_case", "get_review_status_by_application",
    "list_cases", "open_review", "reset",
]


def _json(model: ApiModel) -> dict:
    """The answer as over HTTP: JSON field names, fields that were never set left out."""
    return model.model_dump(mode="json", by_alias=True, exclude_unset=True)


# -- steps for Process Orchestration (README 8): input = JSON body incl. processId and stepRunId ---
def open_review(input: dict | OpenReviewStep) -> dict:
    return _json(services.open_review(input))


def close_review(input: dict | CloseReviewStep) -> dict:
    return _json(services.close_review(input))


# -- queries for other modules (README 9): parameters by their openapi names ------------------------
def get_review_status_by_application(*, applicationId: str, **_other: object) -> dict:
    return _json(services.get_review_status_by_application(applicationId=applicationId))


# -- operations of OSP staff (README 7) -----------------------------------------------------------
def list_cases(status: Sequence[str] | None, kind: Sequence[str] | None, verification: Sequence[str] | None,
               application_id: str | None, page: int, size: int) -> dict:
    return _json(services.list_cases(status, kind, verification, application_id, page, size))


def get_case(case_id: str) -> dict:
    return _json(services.get_case(case_id))


def approve(case_id: str, sub: str, comment: str | None) -> dict:
    return _json(services.approve(case_id, sub, comment))


def decline(case_id: str, sub: str, reason: str) -> dict:
    return _json(services.decline(case_id, sub, reason))

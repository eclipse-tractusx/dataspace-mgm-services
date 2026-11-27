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
"""Business logic of the application review: the automatic pre-check (`checks`) and the review cases
(`review_cases`). No HTTP here; the controllers and `interface.py` call these functions, which return the API
models of `models/`."""
from __future__ import annotations

from ..managers import review_case_repository as _repository
from ..managers.config import config
from .review_cases import (
    approve,
    close_review,
    decline,
    get_case,
    get_review_status_by_application,
    list_cases,
    open_review,
    view,
)


def reset() -> None:
    _repository.reset()


def start() -> None:
    """Start-up: an invalid configuration prevents the start (README 4, 6.6); the tables are created."""
    config()
    _repository.create_tables()


__all__ = [
    "approve", "close_review", "config", "decline", "get_case", "get_review_status_by_application", "list_cases",
    "open_review", "reset", "start", "view",
]

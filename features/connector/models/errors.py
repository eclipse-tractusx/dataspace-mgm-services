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
"""Problem Details of C6-M1 (README 12) and the check of an in-process input against its model."""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from portal_common.problems import Problem

from .connector import MODULE


def problem(status: int, name: str, *, detail: str | None = None, errors: list[dict] | None = None,
            retryable: bool | None = None) -> Problem:
    """`urn:c6-m1:problem:<name>`; `retryable` only where the caller sets it (steps, FRAMEWORK 4.4)."""
    extra: dict = {} if retryable is None else {"retryable": retryable}
    if errors is not None:
        extra["errors"] = errors
    return Problem(MODULE, status, name, detail=detail, **extra)


def parse[M: BaseModel](model: type[M], data: M | dict, *, retryable: bool | None = None) -> M:
    """`data` as `model`: a controller passes the validated model, an in-process caller (Process Orchestration,
    tests) a dict, which is checked here before anything changes (README 8, FRAMEWORK 4.4)."""
    if isinstance(data, model):
        return data
    if not isinstance(data, dict):
        raise problem(400, "validation", detail="JSON object required", retryable=retryable)
    try:
        return model.model_validate(data)
    except ValidationError as e:
        errors = [{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]} for err in e.errors()]
        raise problem(400, "validation", errors=errors, retryable=retryable) from None

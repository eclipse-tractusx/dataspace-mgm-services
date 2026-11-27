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
"""The spec id of the credentials and its Problem Details (README 12, types `urn:c4-m1:problem:...`).

Every Problem of the feature is built here, so the identifiers and their `retryable` flag sit in one place.
"""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from portal_common.problems import Problem

MODULE = "c4-m1"


def _problem(status: int, name: str, detail: str | None, retryable: bool | None = False) -> Problem:
    """A Problem of this module; `retryable=None` leaves the flag to the HTTP layer (set for steps only)."""
    if retryable is None:
        return Problem(MODULE, status, name, detail=detail)
    return Problem(MODULE, status, name, detail=detail, retryable=retryable)


def upstream(detail: str) -> Problem:
    return _problem(502, "upstream-error", detail, retryable=True)


def no_route(detail: str) -> Problem:
    return _problem(409, "no-issuer-route", detail)


def company_not_ready(detail: str) -> Problem:
    return _problem(409, "company-not-ready", detail)


def wallet_not_ready(detail: str) -> Problem:
    return _problem(409, "wallet-not-ready", detail)


def issuer_rejected(detail: str) -> Problem:
    return _problem(409, "issuer-rejected", detail)


def invalid_state(detail: str, retryable: bool | None = None) -> Problem:
    return _problem(409, "invalid-state", detail, retryable)


def unknown_request() -> Problem:
    return _problem(404, "unknown-request", "no order for this BPN and credential type", retryable=None)


def not_found(detail: str) -> Problem:
    return _problem(404, "not-found", detail, retryable=None)


def parse[M: BaseModel](model: type[M], data: object) -> M:
    """`data` as `model`, or 400 `validation` with the fields at fault, as the HTTP layer answers (README 12)."""
    try:
        return model.model_validate(data)
    except ValidationError as e:
        errors = [{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]} for err in e.errors()]
        raise Problem(MODULE, 400, "validation", retryable=False, errors=errors) from None

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
"""Shared building blocks of the feature models (FRAMEWORK 4.1, 4.4).

Every feature defines its own pydantic models in `features/<feature>/models/`. They build on these few
bases, so the conventions every module shares are written once:

- `ApiModel`: snake_case attributes in Python, camelCase fields in JSON (4.1). Input is accepted by either
  name, output always uses the JSON name.
- `RequestBody`: a request body with `additionalProperties: false`; an optional field may be left out but
  must not be sent as `null`.
- `StepRequest` / `StepResult[T]`: the input and the result envelope of every step (4.4).
- `Page[T]`: a list response `{items, page, size, total}` (4.1), with `Page.of()` for in-memory rows.
- `Uuid`, `Bpnl`, `CountryCode`: the identifier formats of the spec. They stay `str`, so a model holds the same
  values the services and repositories already use.

Only feature-independent shapes belong here. A model that one feature owns stays in that feature.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

Uuid = Annotated[str, Field(pattern=UUID_PATTERN)]
"""An identifier as UUID string (FRAMEWORK 4.1)."""

Bpnl = Annotated[str, Field(pattern=r"^BPNL[0-9A-Z]{12}$")]
"""The Business Partner Number of a legal entity."""

CountryCode = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
"""ISO 3166-1 alpha-2 country code."""

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

class ApiModel(BaseModel):
    """Base of every model a feature exposes: snake_case in Python, camelCase in JSON."""

    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, validate_by_alias=True,
                              serialize_by_alias=True, use_enum_values=True)

    def to_json(self) -> dict:
        """The JSON form (camelCase, without unset optional fields) for responses, events and step results."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class RequestBody(ApiModel):
    """A request body with `additionalProperties: false`; leaving out an optional field is fine, `null` is not."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _no_explicit_null(self) -> RequestBody:
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{to_camel(name)} must not be null")
        return self


class StepRequest(ApiModel):
    """Input of every step (FRAMEWORK 4.4); `processId` and `stepRunId` only serve the audit log and tracing.
    Further fields of the call are ignored, so Process Orchestration can pass its whole step input."""

    model_config = ConfigDict(extra="ignore")

    process_id: Uuid
    step_run_id: Uuid


class StepResult[T](ApiModel):
    """Result envelope of every step: `{stepRunId, state, result}`; `RUNNING` only for long-running steps."""

    step_run_id: str | None = None
    state: Literal["DONE", "RUNNING"] = "DONE"
    result: T

    @classmethod
    def done(cls, request: StepRequest | None, result: T) -> StepResult[T]:
        return cls(step_run_id=request.step_run_id if request else None, state="DONE", result=result)

    @classmethod
    def running(cls, request: StepRequest | None, result: T) -> StepResult[T]:
        return cls(step_run_id=request.step_run_id if request else None, state="RUNNING", result=result)


class Page[T](ApiModel):
    """A list response (FRAMEWORK 4.1): `page` counts from 0, `size` is 1 to 100."""

    items: list[T]
    page: int = Field(ge=0)
    size: int = Field(ge=1, le=MAX_PAGE_SIZE)
    total: int = Field(ge=0)

    @classmethod
    def of(cls, rows: Sequence[T], page: int | None = 0, size: int | None = DEFAULT_PAGE_SIZE) -> Page[T]:
        """One page of rows that are already filtered and sorted; slicing is O(size), not O(rows)."""
        page = page or 0
        size = size or DEFAULT_PAGE_SIZE
        start = page * size
        return cls(items=list(rows[start:start + size]), page=page, size=size, total=len(rows))

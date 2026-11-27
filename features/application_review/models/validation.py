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
"""Validation of in-process input (steps called by Process Orchestration without HTTP): a failure is the same
400 `validation` that the HTTP layer answers, with the field and the message, never the input value."""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from .errors import problem


def parse[Model: BaseModel](model: type[Model], data: object) -> Model:
    """`data` as `model`; an instance of the model is passed through unchanged (HTTP already validated it)."""
    if isinstance(data, model):
        return data
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        errors = [{"field": ".".join(str(part) for part in issue["loc"]), "message": issue["msg"]}
                  for issue in exc.errors(include_url=False, include_input=False, include_context=False)]
        raise problem(400, "validation", errors=errors, retryable=False) from exc

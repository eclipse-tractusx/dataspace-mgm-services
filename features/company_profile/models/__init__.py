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
"""Models of the company profile (F16, F17): value sets, the API models of steps and responses
(camelCase in JSON, field names of the spec's openapi.yaml) and the SQLModel tables of README 5.

- `value_sets`: the enums of the spec;
- `company`, `change_request`, `company_role`, `steps`: the response and step result models;
- `tables`: the tables of the feature's own database.
"""
from __future__ import annotations

from pydantic import BaseModel

MODULE = "c3-m1"


def wire(answer):
    """The JSON an in-process caller gets: the same camelCase document the HTTP API sends, `null` fields kept
    (FRAMEWORK 4.4: a step answers the same in-process and over HTTP)."""
    if isinstance(answer, BaseModel):
        return answer.model_dump(mode="json", by_alias=True)
    if isinstance(answer, list):
        return [wire(item) for item in answer]
    return answer

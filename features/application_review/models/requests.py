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
"""Request bodies and step inputs (openapi.yaml `ApproveRequest`, `DeclineRequest`, `StepOpenReview`,
`StepCloseReview`). The two request bodies allow further fields, as the spec does not forbid them."""
from __future__ import annotations

from pydantic import Field

from portal_common.models import ApiModel, StepRequest, Uuid

from .value_sets import ClosureReason


class ApproveRequest(ApiModel):
    comment: str | None = Field(default=None, min_length=1, max_length=1000)


class DeclineRequest(ApiModel):
    reason: str = Field(min_length=1, max_length=1000)


class OpenReviewStep(StepRequest):
    application_id: Uuid


class CloseReviewStep(StepRequest):
    application_id: Uuid
    reason: ClosureReason

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
"""Status of the review case of an application (README 9)."""
from __future__ import annotations

from features.application_review import interface
from features.application_review.models.review_case import ReviewStatusInfo
from portal_common.routing import Controller, Permission

controller = Controller("Application Review: Process Steps and Queries")


@controller.get("", response_model=ReviewStatusInfo, response_model_exclude_unset=True)
def get_review_status_by_application(applicationId: str, _: dict = Permission) -> dict:
    return interface.get_review_status_by_application(applicationId=applicationId)

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
"""The review cases and the decisions of OSP staff (README 7). Every operation has the scope `osp` (README 6.7)."""
from __future__ import annotations

from fastapi import Body, Query

from features.application_review import interface
from features.application_review.models.requests import ApproveRequest, DeclineRequest
from features.application_review.models.review_case import ReviewCase, ReviewCasePage
from features.application_review.models.value_sets import Kind, Status, Verification
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("Application Review: Review Cases")


@controller.get("", response_model=ReviewCasePage, response_model_exclude_unset=True)
def list_review_cases(status: list[Status] | None = Query(None), kind: list[Kind] | None = Query(None),
                      verification: list[Verification] | None = Query(None), applicationId: str | None = None,
                      page: int = Page, size: int = Size, _: dict = Permission) -> dict:
    return interface.list_cases(status, kind, verification, applicationId, page, size)


@controller.get("/{reviewCaseId}", response_model=ReviewCase, response_model_exclude_unset=True)
def get_review_case(reviewCaseId: str, _: dict = Permission) -> dict:
    return interface.get_case(reviewCaseId)


@controller.post("/{reviewCaseId}/approve", response_model=ReviewCase, response_model_exclude_unset=True)
def approve_review_case(reviewCaseId: str, body: ApproveRequest | None = Body(None), claims: dict = Permission) -> dict:
    return interface.approve(reviewCaseId, claims["sub"], body.comment if body else None)


@controller.post("/{reviewCaseId}/decline", response_model=ReviewCase, response_model_exclude_unset=True)
def decline_review_case(reviewCaseId: str, body: DeclineRequest, claims: dict = Permission) -> dict:
    return interface.decline(reviewCaseId, claims["sub"], body.reason)

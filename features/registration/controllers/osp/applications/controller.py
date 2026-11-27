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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""OSP staff read the applications (README 7.12, 7.13)."""
from __future__ import annotations

from fastapi import Query

from features.registration import interface
from features.registration.models.applications import ApplicationSummary, ApplicationWithReview
from features.registration.models.value_sets import ApplicationKind, ApplicationStatus, Verification
from portal_common.models import Page as PageOf
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("Registration: Application Review")


@controller.get("", response_model=PageOf[ApplicationSummary], response_model_exclude_unset=True)
def list_all_applications(status: list[ApplicationStatus] | None = Query(None),
                          kind: list[ApplicationKind] | None = Query(None),
                          verification: list[Verification] | None = Query(None), companyId: str | None = None,
                          page: int = Page, size: int = Size, _: dict = Permission) -> PageOf[ApplicationSummary]:
    return interface.list_all(status, kind, verification, companyId, page, size)


@controller.get("/{applicationId}", response_model=ApplicationWithReview, response_model_exclude_unset=True)
def get_any_application(applicationId: str, _: dict = Permission) -> ApplicationWithReview:
    return interface.get_any_application(applicationId)

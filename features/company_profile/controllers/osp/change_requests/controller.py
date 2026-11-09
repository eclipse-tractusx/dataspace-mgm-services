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
"""OSP staff review change requests (README 7.14, 7.15, 7.17, 7.18)."""
from __future__ import annotations

from fastapi import Body, Query

from features.company_profile.services import change_request_service
from portal_common.routing import Controller, Permission

controller = Controller("Company Profile: Change Request Review")


@controller.get("")
def list_change_requests(status: list[str] | None = Query(None), companyId: str | None = None,
                         page: int = 0, size: int = 20,
                         _: dict = Permission):
    return change_request_service.list_change_requests(status=status, companyId=companyId, page=page, size=size)


@controller.get("/{changeRequestId}")
def get_change_request(changeRequestId: str, _: dict = Permission):
    return change_request_service.get_change_request(changeRequestId)


@controller.post("/{changeRequestId}/approve")
def approve_change_request(changeRequestId: str, body: dict | None = Body(None), claims: dict = Permission):
    return change_request_service.approve_change_request(changeRequestId, body, claims.get("sub"))


@controller.post("/{changeRequestId}/decline")
def decline_change_request(changeRequestId: str, body: dict | None = Body(None), claims: dict = Permission):
    return change_request_service.decline_change_request(changeRequestId, body, claims.get("sub"))

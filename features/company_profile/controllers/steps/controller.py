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
"""The steps of the company profile in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from fastapi import Body

from features.company_profile.services import company_lifecycle_service
from portal_common.routing import Controller, Permission

controller = Controller("Company Profile: Process Steps and Queries")


@controller.post("/create-company")
def create_company(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.create_company(body)


@controller.post("/assign-identifier")
def assign_identifier(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.assign_identifier(body)


@controller.post("/activate-company")
def activate_company(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.activate_company(body)


@controller.post("/deactivate-company")
def deactivate_company(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.deactivate_company(body)


@controller.post("/reactivate-company")
def reactivate_company(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.reactivate_company(body)


@controller.post("/reject-company")
def reject_company(body: dict = Body(...), _: dict = Permission):
    return company_lifecycle_service.reject_company(body)

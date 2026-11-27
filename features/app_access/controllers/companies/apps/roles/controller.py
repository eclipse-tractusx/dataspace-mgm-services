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
#  Assisted-By: GitHub Copilot
#################################################################################
"""App roles of an app for the company (README 7.5), scope `company`."""
from __future__ import annotations

from fastapi import Query

from features.app_access.interface import company_actor, services
from features.app_access.models import CompanyAppRoles
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Permission

controller = Controller("App Access: Company App Roles")


@controller.get("", operation_id="getCompanyAppRoles", response_model=CompanyAppRoles,
                summary="App roles of an app and whether the company can assign them")
@translated
def get_company_app_roles(companyId: str, appId: str, lang: str | None = Query(None),
                          claims: dict = Permission) -> CompanyAppRoles:
    company_actor(claims, companyId)
    return services().users.get_company_app_roles(companyId, appId, lang)

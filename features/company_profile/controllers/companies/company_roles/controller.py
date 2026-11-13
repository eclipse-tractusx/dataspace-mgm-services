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
"""The company roles of the own company (README 7.7 to 7.9), scope `company`."""
from __future__ import annotations

from fastapi import Body

from features.company_profile.services import company_role_service
from features.company_profile.services.shared import MODULE
from portal_common.routing import Controller, Permission, company_scope

controller = Controller("Company Profile: Company Roles")


@controller.get("")
def list_company_roles(companyId: str, lang: str | None = None, claims: dict = Permission):
    company_scope(MODULE, claims, companyId)
    return company_role_service.list_company_roles(companyId, lang)


@controller.post("")
def add_company_role(companyId: str, body: dict = Body(...), lang: str | None = None, claims: dict = Permission):
    company_scope(MODULE, claims, companyId)
    return company_role_service.add_company_role(companyId, body, claims.get("sub"), lang)


@controller.delete("/{companyRole}")
def remove_company_role(companyId: str, companyRole: str, lang: str | None = None, claims: dict = Permission):
    company_scope(MODULE, claims, companyId)
    return company_role_service.remove_company_role(companyId, companyRole, claims.get("sub"), lang)

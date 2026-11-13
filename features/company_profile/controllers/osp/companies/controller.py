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
"""OSP staff search, read, correct and deactivate companies (README 7.10 to 7.13)."""
from __future__ import annotations

from fastapi import Body, Query

from features.company_profile.services import company_lifecycle_service, company_service, company_views
from portal_common.routing import Controller, Permission

controller = Controller("Company Profile: Company Administration")


@controller.get("")
def list_companies(status: list[str] | None = Query(None), name: str | None = None,
                   bpn: str | None = None, hasBpn: bool | None = None,
                   companyRole: str | None = None, coreDataSource: str | None = None,
                   page: int = 0, size: int = 20,
                   _: dict = Permission):
    return company_service.list_companies(status=status, name=name, bpn=bpn, hasBpn=hasBpn,
                                    companyRole=companyRole, coreDataSource=coreDataSource,
                                    page=page, size=size)


@controller.get("/{companyId}")
def read_company(companyId: str, _: dict = Permission):
    return company_views.company_view(companyId, detail=True)


@controller.post("/{companyId}/deactivate")
def deactivate_company_by_staff(companyId: str, body: dict = Body(...), claims: dict = Permission):
    return company_lifecycle_service.deactivate_company_by_staff(companyId, body, claims.get("sub"))


@controller.patch("/{companyId}")
def correct_company(companyId: str, body: dict = Body(...), claims: dict = Permission):
    return company_service.correct_company(companyId, body, claims.get("sub"))

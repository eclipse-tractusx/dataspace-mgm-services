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
"""People of the company (README 7.1, 7.2, 7.4), scope `company`."""
from __future__ import annotations

from fastapi import Query, Response

from features.app_access.interface import company_actor, services
from features.app_access.models import CompanyUser, CompanyUserDetail, Page as Paged
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("App Access: Company Users")


@controller.get("", operation_id="listCompanyUsers", response_model=Paged[CompanyUser],
                summary="List the people of the company")
@translated
def list_company_users(companyId: str, page: int = Page, size: int = Size,
                       status: list[str] | None = Query(None, description="May be given several times."),
                       claims: dict = Permission) -> Paged[CompanyUser]:
    company_actor(claims, companyId)
    return services().users.list_company_users(companyId, status, page, size)


@controller.get("/{userId}", operation_id="getCompanyUser", response_model=CompanyUserDetail,
                summary="One person of the company with portal roles and app roles")
@translated
def get_company_user(companyId: str, userId: str, claims: dict = Permission) -> CompanyUserDetail:
    company_actor(claims, companyId)
    return services().users.get_company_user(companyId, userId)


@controller.delete("/{userId}", status_code=204, operation_id="removeCompanyUser",
                   summary="Remove a person from the company")
@translated
def remove_company_user(companyId: str, userId: str, claims: dict = Permission) -> Response:
    actor = company_actor(claims, companyId)
    services().users.remove_company_user(companyId, userId, actor)
    return Response(status_code=204)

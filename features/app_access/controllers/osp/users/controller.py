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
"""People of all companies for the OSP staff (README 7.11, 7.12), scope `osp`."""
from __future__ import annotations

from fastapi import Query

from features.app_access.interface import services
from features.app_access.models import CompanyUser, UserAccount
from features.app_access.models import Page as Paged
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("App Access: OSP Users")


@controller.get("", operation_id="listUsers", response_model=Paged[CompanyUser],
                summary="List the people of all companies")
@translated
def list_users(page: int = Page, size: int = Size, companyId: str | None = Query(None),
               status: list[str] | None = Query(None, description="May be given several times."),
               claims: dict = Permission) -> Paged[CompanyUser]:
    return services().users.list_company_users(companyId, status, page, size)


@controller.get("/{userId}", operation_id="getUserAccount", response_model=UserAccount,
                summary="Any account of the installation, also without a company")
@translated
def get_user_account(userId: str, claims: dict = Permission) -> UserAccount:
    return services().users.get_user_account(userId)

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
"""People of a company for other modules (README 9.4), `query_c2_m2`. Same answer as the in-process interface."""
from __future__ import annotations

from fastapi import Query

from features.app_access import interface
from portal_common.routing import Controller, Permission

controller = Controller("App Access: Queries")
# A string on purpose: the interface takes `companyId` as str; the pattern rejects non-UUIDs with 400.
UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


@controller.get("", operation_id="listCompanyUserRefs", summary="People of a company, optionally with a portal role")
def list_company_user_refs(companyId: str | None = Query(None, pattern=UUID_PATTERN), portalRole: str | None = None,
                           status: list[str] | None = Query(None, description="May be given several times."),
                           _: dict = Permission) -> list[dict]:
    return interface.list_company_user_refs(companyId=companyId, portalRole=portalRole, status=status)

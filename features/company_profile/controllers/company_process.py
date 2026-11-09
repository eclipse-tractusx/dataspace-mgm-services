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
"""Company profile: steps of Process Orchestration (spec C3-M1 README 8) and internal queries (README 9).
"""
from __future__ import annotations

from fastapi import Body, Query

from features.company_profile.services import company_lifecycle_service, company_query_service
from features.company_profile.services.shared import MODULE
from portal_common.routing import controller_router, permission

router = controller_router(MODULE, "Company Profile: Process Steps and Queries")


# ---------------------------------------------------------------------------------- steps (8)
@router.post("/steps/create-company")
def create_company(body: dict = Body(...),
                   _: dict = permission(MODULE, "POST", "/steps/create-company")):
    return company_lifecycle_service.create_company(body)


@router.post("/steps/assign-identifier")
def assign_identifier(body: dict = Body(...),
                      _: dict = permission(MODULE, "POST", "/steps/assign-identifier")):
    return company_lifecycle_service.assign_identifier(body)


@router.post("/steps/activate-company")
def activate_company(body: dict = Body(...),
                     _: dict = permission(MODULE, "POST", "/steps/activate-company")):
    return company_lifecycle_service.activate_company(body)


@router.post("/steps/deactivate-company")
def deactivate_company(body: dict = Body(...),
                       _: dict = permission(MODULE, "POST", "/steps/deactivate-company")):
    return company_lifecycle_service.deactivate_company(body)


@router.post("/steps/reactivate-company")
def reactivate_company(body: dict = Body(...),
                       _: dict = permission(MODULE, "POST", "/steps/reactivate-company")):
    return company_lifecycle_service.reactivate_company(body)


@router.post("/steps/reject-company")
def reject_company(body: dict = Body(...),
                   _: dict = permission(MODULE, "POST", "/steps/reject-company")):
    return company_lifecycle_service.reject_company(body)


# ------------------------------------------------------------------------- queries (9.2, 9.3, 9.4)
@router.get("/internal/companies")
def query_companies(id: list[str] | None = Query(None), bpn: list[str] | None = Query(None),
                    _: dict = permission(MODULE, "GET", "/internal/companies")):
    return company_query_service.query_companies(id=id, bpn=bpn)


@router.post("/internal/companies/identifier-matches")
def find_identifier_matches(body: dict = Body(...),
                            _: dict = permission(MODULE, "POST",
                                                   "/internal/companies/identifier-matches")):
    return company_query_service.find_identifier_matches(**body)


@router.get("/internal/company-roles")
def query_company_role_catalog(lang: str | None = None,
                               _: dict = permission(MODULE, "GET", "/internal/company-roles")):
    return company_query_service.query_company_role_catalog(lang=lang)


@router.get("/internal/companies/{companyId}")
def query_company(companyId: str,
                  _: dict = permission(MODULE, "GET", "/internal/companies/{companyId}")):
    return company_query_service.query_company(companyId=companyId)

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
"""Registration: reference data for the registration form (spec C1-M2 README 7.1).
"""
from __future__ import annotations

from fastapi import Query

from features.registration.models.value_sets import Lang
from features.registration.services import reference_data_service
from features.registration.services.shared import MODULE
from portal_common.routing import controller_router, permission

router = controller_router(MODULE, "Registration: Reference Data")


# ------------------------------------------------------------------------- reference data (7.1)
@router.get("/countries")
def list_countries(lang: Lang = "en", _: dict = permission(MODULE, "GET", "/countries")):
    return reference_data_service.list_countries(lang)


@router.get("/countries/{countryCode}/identifier-types")
def list_identifier_types(countryCode: str, lang: Lang = "en",
                          _: dict = permission(MODULE, "GET", "/countries/{countryCode}/identifier-types")):
    return reference_data_service.list_identifier_types(countryCode, lang)


@router.get("/company-roles")
def list_company_roles(lang: Lang = "en", _: dict = permission(MODULE, "GET", "/company-roles")):
    return reference_data_service.list_company_roles(lang)


@router.get("/agreements")
def list_agreements(companyRole: list[str] | None = Query(None), lang: Lang = "en",
                    _: dict = permission(MODULE, "GET", "/agreements")):
    return reference_data_service.list_agreements(companyRole or [], lang)

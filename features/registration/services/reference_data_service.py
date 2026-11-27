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
"""Reference data for the registration form: countries, identifier types, company roles, agreements (7.1).
"""
from __future__ import annotations

from collections import defaultdict

from features.registration.managers import agreement_repository, reference_catalog
from features.registration.models import errors as problems
from features.registration.models.reference_data import Agreement, CompanyRoleInfo, Country, IdentifierTypeInfo
from features.registration.models.value_sets import AgreementStatus
from features.registration.services.shared import field_error, validation_problem


def _text(texts: dict, lang: str) -> str:
    """The text in the requested language, English when there is none."""
    return texts.get(lang) or texts["en"]


def list_countries(lang: str) -> list[Country]:
    countries = sorted(reference_catalog.master()["countries"], key=lambda c: c["code"])
    return [Country(code=c["code"], name=_text(c["name"], lang)) for c in countries]


def list_identifier_types(country_code: str, lang: str) -> list[IdentifierTypeInfo]:
    country = reference_catalog.country(country_code)
    if country is None:
        raise problems.not_found()
    allowed = set(country.get("identifierTypes", []))
    return [IdentifierTypeInfo(type=t["type"], name=_text(t["name"], lang),
                               pattern=reference_catalog.identifier_pattern(t["type"], country_code))
            for t in reference_catalog.master()["identifierTypes"] if t["type"] in allowed]


def list_company_roles(lang: str) -> list[CompanyRoleInfo]:
    keys: dict[str, list[str]] = defaultdict(list)
    for a in agreement_repository.versions(AgreementStatus.ACTIVE):
        for role in a.company_roles:
            keys[role].append(a.agreement_key)
    return [CompanyRoleInfo(role=r["role"], name=_text(r["name"], lang), description=_text(r["description"], lang),
                            agreement_keys=keys[r["role"]])
            for r in reference_catalog.roles() if r.get("selectable")]


def list_agreements(company_roles: list[str], lang: str) -> list[Agreement]:
    bad = [r for r in company_roles if not reference_catalog.selectable(r)]
    if bad:
        raise validation_problem([field_error("companyRole", f"unknown or not selectable role: {r}") for r in bad])
    return [Agreement(agreement_key=a.agreement_key, version=a.version, party=a.party, scope=a.scope,
                      title=_text(a.title, lang), document_urls=a.document_urls, company_roles=a.company_roles)
            for a in agreement_repository.required(company_roles)]

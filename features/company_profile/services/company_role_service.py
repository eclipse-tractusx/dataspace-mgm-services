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
"""Company roles of a company and the agreements they need (README 7.7 to 7.9).
"""
from __future__ import annotations

from features.company_profile import config
from features.company_profile.managers import company_repository
from features.company_profile.services import company_validation
from features.company_profile.services.company_views import get_company
from features.company_profile.services.shared import MODULE, utc_now
from portal_common import events, neighbours
from portal_common.problems import Problem
from tools import testdata


# ------------------------------------------------------------------------------ company roles (7.7 - 7.9)
def _terms() -> list[dict]:
    """Active terms of C1-M2 with scope COMPANY_ROLE (11.1); unreachable stays 502."""
    config.apply_registration_url()
    if neighbours.is_standin("c1-m2"):
        agreements = testdata.agreements()
    else:
        agreements = neighbours.query(MODULE, "c1-m2", "list_agreements_internal") or []
    return [agreement for agreement in agreements if agreement.get("scope") == "COMPANY_ROLE"]


def _role_state(company: str, lang: str) -> list[dict]:
    """`CompanyRoleState` of 7.7: catalogue roles plus the roles the company has or had."""
    terms = _terms()
    roles: dict[str, set[str]] = {}
    for role in config.roles_assignable_by_company():
        roles.setdefault(role, set())
    for role in company_repository.list_roles(company):
        roles.setdefault(role, set())
    states = []
    for role in sorted(roles):
        entry = config.role_catalogue().get(role) or {}
        assigned = company_repository.role_status(company, role)
        own = {consent["agreement_key"]: consent for consent in company_repository.list_consents(company)}
        states.append({
            "companyRole": role, "assignableBy": entry.get("assignableBy"),
            "status": "NONE" if assigned == "NONE" else assigned,
            "description": config.description(role, lang) or "",
            "agreements": [{"agreementKey": term["agreementKey"], "version": term["version"],
                            "name": (term.get("title") or {}).get(lang) or (term.get("title") or {}).get("en"),
                            "names": term.get("title") or {},
                            "documentUrl": (term.get("documentUrls") or {}).get(lang)
                            or (term.get("documentUrls") or {}).get("en"),
                            "consentStatus": (own.get(term["agreementKey"]) or {}).get("status"),
                            "consentedVersion": (own.get(term["agreementKey"]) or {}).get("agreement_version"),
                            "consentedAt": (own.get(term["agreementKey"]) or {}).get("consented_at")}
                           for term in terms if role in (term.get("companyRoles") or [])],
        })
    return states


def list_company_roles(companyId: str, lang: str | None = None) -> list[dict]:
    """7.7"""
    get_company(companyId)
    return _role_state(companyId, lang or "en")


def _terms_of(role: str, terms: list[dict]) -> dict[str, dict]:
    """agreementKey -> active term of the role."""
    return {term["agreementKey"]: term for term in terms
            if role in (term.get("companyRoles") or [])}


def add_company_role(companyId: str, body: dict, sub: str | None = None,
                     lang: str | None = None) -> list[dict]:
    """7.8"""
    role = body.get("companyRole") or ""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        errors = company_validation.validate_company_role(role, config.role_catalogue())
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)
        if config.assignable_by(role) != "COMPANY":
            raise Problem(MODULE, 409, "role-not-assignable")
        if company_repository.role_status(companyId, role) == "ACTIVE":
            return _role_state(companyId, lang or "en")

        terms = _terms_of(role, _terms())
        given = {consent.get("agreementKey"): consent for consent in body.get("consents") or []}
        missing = sorted(key for key in terms if (given.get(key) or {}).get("version") != terms[key]["version"])
        if missing:
            raise Problem(MODULE, 400, "consent-missing", missing=missing)
        foreign = sorted(set(given) - set(terms))
        if foreign:
            raise Problem(MODULE, 400, "validation",
                          errors=[{"field": "consents", "reason": f"not a term of {role}: {', '.join(foreign)}"}])

        now = utc_now()
        for key in terms:
            company_repository.set_consent(companyId, key, version=terms[key]["version"], status="ACTIVE",
                              source_kind="COMPANY", consented_by=sub, consented_at=now)
        company_repository.add_role(companyId, role, status="ACTIVE", source_kind="COMPANY", source_ref=sub)
        active = [name for name, status in company_repository.list_roles(companyId).items() if status == "ACTIVE"]
        company_repository.audit(companyId, sub, "addCompanyRole", role, {"companyRole": role})
        events.publish(MODULE, "CompanyRolesChanged", {"companyId": companyId, "companyRoles": active})
    return _role_state(companyId, lang or "en")


def remove_company_role(companyId: str, companyRole: str, sub: str | None = None,
                        lang: str | None = None) -> list[dict]:
    """7.9"""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        if companyRole not in config.role_catalogue():
            raise Problem(MODULE, 404, "not-found")
        if config.assignable_by(companyRole) != "COMPANY":
            raise Problem(MODULE, 409, "role-not-assignable")
        if company_repository.role_status(companyId, companyRole) != "ACTIVE":
            return _role_state(companyId, lang or "en")
        remaining = [role for role, status in company_repository.list_roles(companyId).items()
                     if status == "ACTIVE" and role != companyRole and config.assignable_by(role) == "COMPANY"]
        if not remaining:
            raise Problem(MODULE, 409, "last-role")

        company_repository.remove_role(companyId, companyRole)
        for term in _terms_of(companyRole, _terms()).values():
            others = [role for role, status in company_repository.list_roles(companyId).items()
                      if status == "ACTIVE" and companyRole != role
                      and term["agreementKey"] in [t["agreementKey"] for t in _terms_of(role, _terms()).values()]]
            if not others:
                company_repository.set_consent(companyId, term["agreementKey"], status="INACTIVE",
                                  source_kind="COMPANY", source_ref=sub)
        active = [name for name, status in company_repository.list_roles(companyId).items() if status == "ACTIVE"]
        company_repository.audit(companyId, sub, "removeCompanyRole", companyRole, {"companyRole": companyRole})
        events.publish(MODULE, "CompanyRolesChanged", {"companyId": companyId, "companyRoles": active})
    return _role_state(companyId, lang or "en")

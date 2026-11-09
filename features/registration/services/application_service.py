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
"""Applications of people (README 7.2 to 7.6, 7.10, 7.11) and the read paths of OSP staff (7.12, 7.13).

The scope `own` is applied here: another person's application answers 404 (README 6.3).
"""
from __future__ import annotations

import os
import uuid

from features.registration.managers import neighbour_client, reference_catalog
from features.registration.managers.application_repository import (
    application_sequence,
    applications,
    applications_lock,
    used_jtis,
)
from features.registration.services import attestation_verifier
from features.registration.services.application_validation import (
    check_company_fields,
    check_create,
    check_reference_data,
    check_roles,
)
from features.registration.services.application_views import public, summary
from features.registration.services.company_data import (
    build_company_data,
    check_existing_identifiers,
    company_data_ebw,
    company_for_reference,
    given_identifiers,
    new_company_id,
)
from features.registration.services.shared import (
    ATTESTATION_MAX_CHARS,
    MODULE,
    field_error,
    paginate,
    utc_now,
    validation_problem,
    write_audit,
)
from portal_common import events
from portal_common.problems import Problem

OPEN = ("CREATED", "SUBMITTED")


# --------------------------------------------------------------------------- applications (7.2 to 7.11)
def _open_of(sub: str) -> dict | None:
    return next((a for a in applications.values() if a["applicant"]["sub"] == sub and a["status"] in OPEN), None)


def create_application(body: dict, claims: dict) -> tuple[dict, bool]:
    """7.2, in the order of the README. Returns the application and whether it is new (201) or a repetition (200)."""
    if claims.get("company_id"):
        raise Problem(MODULE, 403, "account-bound")
    check_create(body)
    kind, verification = body["kind"], body["verification"]
    if verification == "DOCUMENTS" and os.environ.get("DOCUMENTS_ENABLED", "true").lower() == "false":
        raise Problem(MODULE, 400, "documents-disabled")
    header, payload = attestation_verifier.verify(body["attestation"], claims) if verification == "EBW" else (None, None)
    sub = claims["sub"]
    with applications_lock:
        existing = _open_of(sub)
        if existing:
            if payload and existing.get("_attestation") and existing["_attestation"]["attestationId"] == payload["jti"]:
                return public(existing), False
            raise Problem(MODULE, 409, "open-application-exists", existingApplicationId=existing["id"])
        if payload and payload["jti"] in used_jtis:
            raise Problem(MODULE, 409, "attestation-used")
    given = body.get("companyData") or {}
    company = company_for_reference(body, kind) if (body.get("companyId") or body.get("bpn")) else None
    company_claim = (payload or {}).get("company")
    company_roles = body.get("companyRoles")
    if company:
        euid = (company_claim or {}).get("euid") or given_identifiers(given).get("EUID")
        check_existing_identifiers(company, (company_claim or {}).get("ebwoid"), euid)
        if not company_roles:
            company_roles = [r for r in company.get("companyRoles") or [] if reference_catalog.selectable(_role_name(r))]
            company_roles = [_role_name(r) for r in company_roles]
            if not company_roles:
                raise validation_problem([field_error("companyRoles", "the company has no selectable roles: give the roles")])
    data, comparison = build_company_data(verification, company_claim, given)
    check_reference_data(data, company_roles, verification)
    with applications_lock:
        existing = _open_of(sub)   # concurrent creation: the same answer as above
        if existing:
            raise Problem(MODULE, 409, "open-application-exists", existingApplicationId=existing["id"])
        if payload and payload["jti"] in used_jtis:
            raise Problem(MODULE, 409, "attestation-used")
        if company and any(a["companyId"] == company["id"] and a["status"] in OPEN for a in applications.values()):
            raise Problem(MODULE, 409, "company-has-open-application")
        now = utc_now()
        a = {"id": str(uuid.uuid4()),
             "companyId": company["id"] if company else new_company_id((company_claim or {}).get("ebwoid")),
             "kind": kind, "existingCompany": bool(company), "verification": verification,
             "applicant": {"sub": sub, "givenName": claims.get("given_name"), "familyName": claims.get("family_name")},
             "status": "CREATED", "companyData": data, "companyRoles": list(company_roles), "comparison": comparison,
             "documents": [], "representationDeclared": None, "consents": [], "declineReason": None, "createdAt": now,
             "changedAt": now, "submittedAt": None, "withdrawnAt": None, "closedAt": None, "completedAt": None,
             "_seq": next(application_sequence), "_given": given, "_files": {}, "_requiredAgreements": [], "_consentRecords": [],
             "_companyRef": bool(company)}
        if payload:
            a |= {"_attestation": attestation_verifier.summary(header, payload), "_raw": body["attestation"],
                  "_attestationClaims": {"iat": payload["iat"], "exp": payload["exp"], "company": company_claim}}
            used_jtis.add(payload["jti"])
        applications[a["id"]] = a
        write_audit(a, "createApplication", sub=sub)
        events.publish(MODULE, "ApplicationCreated", {"applicationId": a["id"], "companyId": a["companyId"], "kind": kind,
                                                      "existingCompany": a["existingCompany"]})
        return public(a), True


def _role_name(role: object) -> str:
    """Company roles of C3-M1 come as names or as `{companyRole, status}`."""
    return role.get("companyRole") if isinstance(role, dict) else role


def own(sub: str, application_id: str) -> dict:
    """Scope `own` (6.3): for other people the application does not exist."""
    a = applications.get(application_id)
    if not a or a["applicant"]["sub"] != sub:
        raise Problem(MODULE, 404, "not-found")
    return a


def any_application(application_id: str) -> dict:
    a = applications.get(application_id)
    if not a:
        raise Problem(MODULE, 404, "not-found")
    return a


def list_own(sub: str, status: list[str] | None, page: int, size: int) -> dict:
    found = sorted((a for a in applications.values() if a["applicant"]["sub"] == sub and (not status or a["status"] in status)),
                   key=lambda a: a["_seq"], reverse=True)
    return paginate([summary(a) for a in found], page, size)


def list_all(status: list[str] | None, kind: list[str] | None, verification: list[str] | None, company_id: str | None,
             page: int, size: int) -> dict:
    found = sorted((a for a in applications.values() if (not status or a["status"] in status) and (not kind or a["kind"] in kind)
                    and (not verification or a["verification"] in verification)
                    and (not company_id or a["companyId"] == company_id)), key=lambda a: a["_seq"], reverse=True)
    return paginate([summary(a) for a in found], page, size)


def update_application(application_id: str, sub: str, body: dict) -> dict:
    """7.5."""
    a = own(sub, application_id)
    if a["status"] != "CREATED":
        raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
    allowed = ("legalName", "shortName", "address", "identifiers", "companyRoles")
    change = {k: body[k] for k in allowed if k in body}
    if not change:
        raise validation_problem([field_error("body", f"at least one of {', '.join(allowed)}")])
    errors: list[dict] = [field_error(k, "must not be null") for k in ("legalName", "address", "identifiers")
                          if k in change and change[k] is None]
    check_company_fields(change, errors)
    if "companyRoles" in change:
        check_roles(change["companyRoles"], errors)
    if a["verification"] == "DOCUMENTS" and change.get("identifiers") == []:
        errors.append(field_error("identifiers", "at least one identifier for DOCUMENTS"))
    if errors:
        raise validation_problem(errors)
    company_claim = (a.get("_attestationClaims") or {}).get("company")
    given = {**a["_given"], **{k: v for k, v in change.items() if k != "companyRoles"}}
    if "identifiers" in change and a["_companyRef"]:
        company = neighbour_client.company_by_id(a["companyId"]) or {}
        euid = (company_claim or {}).get("euid") or given_identifiers(given).get("EUID")
        check_existing_identifiers(company, (company_claim or {}).get("ebwoid"), euid)
    data, comparison = build_company_data(a["verification"], company_claim, given)
    roles = change.get("companyRoles", a["companyRoles"])
    check_reference_data(data, roles, a["verification"])
    with applications_lock:
        if a["status"] != "CREATED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        a.update(companyData=data, comparison=comparison, companyRoles=list(roles), changedAt=utc_now(), _given=given)
        write_audit(a, "updateApplication", sub=sub)
        return public(a)


def replace_attestation(application_id: str, claims: dict, token: object) -> dict:
    """7.6."""
    sub = claims["sub"]
    a = own(sub, application_id)
    if a["status"] != "CREATED" or a["verification"] == "DOCUMENTS":
        raise Problem(MODULE, 409, "invalid-state", detail="only in status CREATED and the verification path EBW")
    if not (isinstance(token, str) and 0 < len(token) <= ATTESTATION_MAX_CHARS):
        raise validation_problem([field_error("attestation", "required, at most 16 KB")])
    header, payload = attestation_verifier.verify(token, claims)
    if a["_attestation"]["attestationId"] == payload["jti"]:
        return public(a)
    new, old = payload["company"], a["_attestationClaims"]["company"]
    fields = []
    if new["ebwoid"] != old["ebwoid"]:
        fields.append("EBWOID")
    if new["country"] != old["country"]:
        fields.append("COUNTRY")
    applicant_euid = given_identifiers(a["_given"]).get("EUID")
    euid = reference_catalog.normalise_identifier("EUID", new["euid"]) if new.get("euid") else None
    if euid and ((old.get("euid") and reference_catalog.normalise_identifier("EUID", old["euid"]) != euid)
                 or (applicant_euid and applicant_euid != euid)):
        fields.append("EUID")
    if fields:
        raise Problem(MODULE, 400, "attestation-mismatch", fields=fields)
    data, comparison = company_data_ebw(new, a["_given"])
    check_reference_data(data, a["companyRoles"], a["verification"])
    if a["_companyRef"]:
        check_existing_identifiers(neighbour_client.company_by_id(a["companyId"]) or {}, new["ebwoid"], euid or applicant_euid)
    with applications_lock:
        if payload["jti"] in used_jtis:
            raise Problem(MODULE, 409, "attestation-used")
        if a["status"] != "CREATED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        used_jtis.add(payload["jti"])
        a.update(companyData=data, comparison=comparison, changedAt=utc_now(), _attestation=attestation_verifier.summary(header, payload),
                 _raw=token, _attestationClaims={"iat": payload["iat"], "exp": payload["exp"], "company": new})
        write_audit(a, "replaceAttestation", sub=sub)
        return public(a)


def submit_application(application_id: str, sub: str, body: dict) -> dict:
    """7.10."""
    with applications_lock:
        a = own(sub, application_id)
        if a["status"] == "SUBMITTED":
            return public(a)
        if a["status"] != "CREATED":
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        consents = body.get("consents")
        valid = isinstance(consents, list) and consents and all(
            isinstance(c, dict) and isinstance(c.get("agreementKey"), str) and isinstance(c.get("version"), str)
            and c.get("language") in ("de", "en") for c in consents)
        if not valid:
            raise validation_problem([field_error("consents", "at least one consent with agreementKey, version and language de or en")])
        if a["verification"] == "EBW" and not attestation_verifier.usable_at_submission(a):
            raise Problem(MODULE, 409, "attestation-expired")
        if a["verification"] == "DOCUMENTS":
            types = {d["documentType"] for d in a["documents"]}
            missing_types = [] if "COMMERCIAL_REGISTER_EXTRACT" in types else ["COMMERCIAL_REGISTER_EXTRACT"]
            undeclared = body.get("representationDeclared") is not True
            if missing_types or undeclared:
                raise Problem(MODULE, 400, "documents-incomplete", missingDocumentTypes=missing_types,
                              representationDeclarationMissing=undeclared)
        required = [{"agreementKey": x["agreementKey"], "version": x["version"]} for x in reference_catalog.required(a["companyRoles"])]
        given = {(c["agreementKey"], c["version"]) for c in consents}
        missing = [r for r in required if (r["agreementKey"], r["version"]) not in given]
        if missing:
            raise Problem(MODULE, 400, "consents-incomplete", missing=missing)
        needed = {(r["agreementKey"], r["version"]) for r in required}
        extra = [c["agreementKey"] for c in consents if (c["agreementKey"], c["version"]) not in needed]
        if extra:
            raise validation_problem([field_error("consents", f"unknown or not required terms: {k}") for k in extra])
        now = utc_now()
        a.update(consents=[{"agreementKey": c["agreementKey"], "version": c["version"], "language": c["language"], "givenAt": now}
                           for c in consents],
                 status="SUBMITTED", submittedAt=now, changedAt=now, _requiredAgreements=required,
                 _consentRecords=[{"agreementKey": c["agreementKey"], "version": c["version"], "language": c["language"],
                                   "givenAt": now, "givenBySub": sub,
                                   "attestationId": (a.get("_attestation") or {}).get("attestationId")} for c in consents])
        if a["verification"] == "DOCUMENTS":
            a["representationDeclared"] = True
        write_audit(a, "submitApplication", sub=sub)
        events.publish(MODULE, "ApplicationSubmitted", {"applicationId": a["id"], "companyId": a["companyId"], "kind": a["kind"],
                                                        "existingCompany": a["existingCompany"], "applicantSub": sub})
        return public(a)


def withdraw_application(application_id: str, sub: str) -> dict:
    """7.11."""
    a = own(sub, application_id)
    if a["status"] == "WITHDRAWN":
        return public(a)
    if a["status"] not in OPEN:
        raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
    if a["status"] == "SUBMITTED":
        review = neighbour_client.review_status(a["id"])   # not reachable: 502, nothing changed
        if review in ("APPROVED", "DECLINED"):
            raise Problem(MODULE, 409, "already-decided", reviewStatus=review)
    with applications_lock:
        if a["status"] == "WITHDRAWN":
            return public(a)
        if a["status"] not in OPEN:
            raise Problem(MODULE, 409, "invalid-state", detail=f"application is {a['status']}")
        submitted = a["status"] == "SUBMITTED"
        now = utc_now()
        a.update(status="WITHDRAWN", withdrawnAt=now, changedAt=now)
        write_audit(a, "withdrawApplication", sub=sub)
        if submitted:
            events.publish(MODULE, "ApplicationWithdrawn", {"applicationId": a["id"], "companyId": a["companyId"], "kind": a["kind"],
                                                            "existingCompany": a["existingCompany"]})
        return public(a)

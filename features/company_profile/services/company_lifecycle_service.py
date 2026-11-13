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
"""Lifecycle of a company along the onboarding flows: create, assign the identifier (BPN), activate,
reject, deactivate and reactivate (steps of README 8, staff deactivation 7.13), and the seed data (README 4).

Steps are idempotent (FRAMEWORK 4.4): the business key is looked up first, only what is missing is
created, a repetition returns the stored result and publishes nothing. Every changing operation
writes the audit log of README 5 and FRAMEWORK 4.3 before it publishes.
"""
from __future__ import annotations

import json

from features.company_profile import config
from features.company_profile.managers import company_repository
from features.company_profile.services import attestation_verifier, company_validation
from features.company_profile.services.company_changes import CORE_IDENTIFIERS, changed_fields
from features.company_profile.services.company_views import active_roles, company_view, get_company
from features.company_profile.services.shared import MODULE, audit_step, utc_now
from portal_common import events, neighbours, standin
from portal_common.problems import Problem
from tools import testdata


# ------------------------------------------------------------------------ start and seed (README 4)
def reset_with_seed() -> None:
    """Empty state, then the seed data of the OSP company (README 4). Seed data has no events."""
    try:
        company_repository.reset()
        target = company_repository
    except Problem as error:
        if error.status != 501:
            raise
        # the start survives an unusable database; the seed then lands in memory, calls answer 501
        target = company_repository.backend_memory()
        target.reset()
    attestation_verifier.reset()
    seed = config.seed_company()
    if not seed or target.get_company(config.osp_company_id()) is not None:
        return
    address = seed.get("address") or {}
    target.create_company({
        "id": seed["companyId"], "name": seed["name"], "bpn": seed.get("bpn"),
        "street": address.get("street"), "house_number": address.get("houseNumber"),
        "postal_code": address.get("postalCode"), "city": address.get("city"),
        "region": address.get("region"), "country_code": address.get("countryCode"),
        "status": "ACTIVE", "core_data_source": "MANUAL",
    })
    target.set_identifiers(seed["companyId"], seed.get("identifiers") or [])
    for role in seed.get("companyRoles") or []:
        target.add_role(seed["companyId"], role, status="ACTIVE", source_kind="SEED",
                        source_ref="ospCompanyFile")


# ----------------------------------------------------------------------------------- steps (8.1)
def _stub_applications() -> dict[str, dict]:
    """Built-in stand-in for C1-M2 (11.1): `STUB_APPLICATIONS_FILE` in `ApplicationInternal` form."""
    path = config.stub_applications_file()
    if path is None:
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    entries = document.get("applications") if isinstance(document, dict) else document
    return {entry["id"]: entry for entry in entries or []}


def _application(application_id: str | None) -> dict:
    config.apply_registration_url()
    """The application at C1-M2 (11.1); a failed call is an error, not "not found" (skill 5)."""
    if neighbours.is_standin("c1-m2"):
        application = _stub_applications().get(application_id or "")
        if application is None:
            raise Problem(MODULE, 404, "not-found", detail="application unknown", retryable=False)
        return application
    try:
        application = neighbours.query(MODULE, "c1-m2", "get_application_internal",
                                       applicationId=application_id)
    except Problem:
        raise
    if not application:
        raise Problem(MODULE, 404, "not-found", detail="application unknown", retryable=False)
    return application


def create_company(input: dict) -> dict:
    """8.1: create the company `REQUESTED` from a submitted application of kind ONBOARDING/TRANSFER."""
    cid, application_id = input.get("companyId"), input.get("applicationId")
    existing = company_repository.get_company(cid)
    if existing is not None:
        if existing["application_id"] == application_id:
            return standin.step_reply(input, {"companyId": cid, "status": existing["status"],
                                              "bpn": existing["bpn"],
                                              "coreDataSource": existing["core_data_source"]})
        raise Problem(MODULE, 409, "conflict", detail="company belongs to another application",
                      retryable=False)

    application = _application(application_id)
    if application.get("companyId") != cid:
        raise Problem(MODULE, 409, "conflict", detail="application has another companyId",
                      retryable=False)
    if application.get("kind") == "REACTIVATION":
        raise Problem(MODULE, 409, "conflict", detail="reactivation uses reactivate-company",
                      retryable=False)
    if application.get("status") not in ("SUBMITTED", "APPROVED"):
        raise Problem(MODULE, 409, "invalid-state",
                      detail=f"application {application.get('status')}", retryable=False)

    data = application.get("companyData") or {}
    source_address = data.get("address") or {}
    verification = application.get("verification")
    row = {"name": data.get("legalName"), "short_name": data.get("shortName"),
           "street": source_address.get("streetName"), "house_number": source_address.get("streetNumber"),
           "postal_code": source_address.get("postalCode"), "city": source_address.get("city"),
           "region": source_address.get("region"), "country_code": source_address.get("countryCode")}
    identifiers = [{"type": entry["type"], "value": entry["value"],
                    "source": "BUSINESS_WALLET" if entry.get("source") == "ATTESTATION" else "DECLARED"}
                   for entry in data.get("identifiers") or []]
    roles = [role for role in application.get("companyRoles") or []
             if config.assignable_by(role) == "COMPANY"]

    errors = company_validation.validate_company(row)
    errors += company_validation.validate_identifiers(identifiers, row["country_code"])
    for role in application.get("companyRoles") or []:
        errors += company_validation.validate_company_role(role, config.role_catalogue())
    if verification == "EBW" and not any(entry["type"] == "EBWOID" for entry in identifiers):
        errors.append({"field": "identifiers", "reason": "EBWOID required with a verification"})
    if errors:
        raise Problem(MODULE, 400, "validation", errors=errors, retryable=False)

    attestation = application.get("attestation") or {}
    with company_repository.lock(cid):
        company_repository.create_company(row | {
            "id": cid, "status": "REQUESTED",
            "core_data_source": "EBW" if verification == "EBW" else "MANUAL",
            "core_data_verified_at": attestation.get("verifiedAt") if verification == "EBW" else None,
            "verification_ref": attestation.get("attestationId") if verification == "EBW" else None,
            "application_id": application_id,
        })
        company_repository.set_identifiers(cid, identifiers)
        for role in roles:
            company_repository.add_role(cid, role, status="REQUESTED", source_kind="APPLICATION",
                           source_ref=application_id)
        audit_step(cid, "stepCreateCompany", input, {"applicationId": application_id})
        created = get_company(cid)
        events.publish(MODULE, "CompanyCreated", {"companyId": cid, "applicationId": application_id,
                                                  "coreDataSource": created["core_data_source"]})
    return standin.step_reply(input, {"companyId": cid, "status": created["status"],
                                      "bpn": created["bpn"],
                                      "coreDataSource": created["core_data_source"]})


# ----------------------------------------------------------------------------------- steps (8.2)
def assign_identifier(input: dict) -> dict:
    """8.2: take over the BPN from `CompanyRegisteredAtCsp`."""
    cid, raw = input.get("companyId"), input.get("bpn") or ""
    with company_repository.lock(cid):
        row = get_company(cid)
        errors = company_validation.validate_bpn(raw)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors, retryable=False)
        bpn = raw.strip().upper()
        if row["bpn"]:
            if row["bpn"] == bpn:
                return standin.step_reply(input, {"companyId": cid, "status": row["status"], "bpn": bpn})
            raise Problem(MODULE, 409, "bpn-mismatch", detail=f"company has {row['bpn']}",
                          retryable=False)
        if row["status"] != "REQUESTED":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        taken = next((other for other in company_repository.find_companies(bpn=bpn, size=5)[0]
                      if other["id"] != cid and other["status"] != "REJECTED"), None)
        if taken is not None:
            raise Problem(MODULE, 409, "bpn-taken", detail=taken["id"], retryable=False)
        company_repository.update_company(cid, bpn=bpn, bpn_assigned_at=utc_now())
        audit_step(cid, "stepAssignIdentifier", input, {"bpn": bpn})
        events.publish(MODULE, "CompanyIdentifierAssigned", {"companyId": cid, "bpn": bpn})
    return standin.step_reply(input, {"companyId": cid, "status": row["status"], "bpn": bpn})


# ----------------------------------------------------------------------------------- steps (8.3)
def _terms_of_roles() -> dict[str, set[str]]:
    config.apply_registration_url()
    """agreementKey -> roles it belongs to, from the terms of C1-M2 (11.1).

    Without an address for C1-M2 the built-in stand-in answers with the initial values of 14.3.
    """
    if neighbours.is_standin("c1-m2"):
        agreements = testdata.agreements()
    else:
        agreements = neighbours.query(MODULE, "c1-m2", "list_agreements_internal") or []
    terms: dict[str, set[str]] = {}
    for agreement in agreements:
        if agreement.get("scope") != "COMPANY_ROLE":
            continue
        for role in agreement.get("companyRoles") or []:
            terms.setdefault(agreement["agreementKey"], set()).add(role)
    return terms


def activate_company(input: dict) -> dict:
    """8.3: activate, taking over the consents of the application."""
    cid, application_id = input.get("companyId"), input.get("applicationId")
    with company_repository.lock(cid):
        row = get_company(cid)
        if row["status"] == "ACTIVE":
            return standin.step_reply(input, {"companyId": cid, "status": row["status"],
                                              "bpn": row["bpn"],
                                              "companyRoles": active_roles(cid),
                                              "pendingCompanyRoles": []})
        if row["status"] in ("REJECTED", "INACTIVE"):
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        if not row["bpn"]:
            raise Problem(MODULE, 409, "identifier-missing", retryable=False)
        if application_id != row["application_id"]:
            raise Problem(MODULE, 409, "conflict", detail="application does not match",
                          retryable=False)

        application = _application(application_id)
        terms = _terms_of_roles()
        given = {consent.get("agreementKey"): consent for consent in application.get("consents") or []}
        active, pending = [], []
        for role, status in company_repository.list_roles(cid).items():
            if status != "REQUESTED":
                continue
            needed = {key for key, roles in terms.items() if role in roles}
            if needed <= set(given):
                active.append(role)
            else:
                pending.append(role)
        if not active:
            raise Problem(MODULE, 409, "roles-without-consent", missing=sorted(pending),
                          retryable=False)

        applicant = (application.get("applicant") or {}).get("sub")
        for role in active:
            company_repository.add_role(cid, role, status="ACTIVE", source_kind="APPLICATION",
                           source_ref=application_id)
            for key in (key for key, roles in terms.items() if role in roles):
                company_repository.set_consent(cid, key, version=given[key].get("version"), status="ACTIVE",
                                  source_kind="APPLICATION", source_ref=application_id,
                                  consented_by=applicant, consented_at=given[key].get("givenAt"))
        fields = {"status": "ACTIVE", "activated_at": utc_now()}
        if row["core_data_source"] == "MANUAL" and not row["core_data_verified_at"]:
            fields["core_data_verified_at"] = utc_now()
        company_repository.update_company(cid, **fields)
        audit_step(cid, "stepActivateCompany", input, {"applicationId": application_id,
                                                   "companyRoles": sorted(active)})
        events.publish(MODULE, "CompanyActivated", {"companyId": cid, "bpn": row["bpn"],
                                                    "companyRoles": sorted(active)})
    return standin.step_reply(input, {"companyId": cid, "status": "ACTIVE", "bpn": row["bpn"],
                                      "companyRoles": sorted(active), "pendingCompanyRoles": pending})


# ----------------------------------------------------------------------------------- steps (8.4)
def reject_company(input: dict) -> dict:
    """8.4: `REJECTED`, final; an assigned BPN becomes free."""
    cid = input.get("companyId")
    with company_repository.lock(cid):
        row = get_company(cid)
        if row["status"] == "REJECTED":
            return standin.step_reply(input, {"companyId": cid, "status": row["status"]})
        if row["status"] in ("ACTIVE", "INACTIVE"):
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        company_repository.update_company(cid, status="REJECTED", rejected_at=utc_now())
        audit_step(cid, "stepRejectCompany", input)
        events.publish(MODULE, "CompanyRejected", {"companyId": cid})
    return standin.step_reply(input, {"companyId": cid, "status": "REJECTED"})


# ---------------------------------------------------------------- deactivation and return (7.13, 8.5, 8.6)
def deactivate_company(input: dict) -> dict:
    """8.5: deactivation by Process Orchestration with reason `MANUAL` or `TRANSFERRED`."""
    cid, reason = input.get("companyId"), input.get("reason")
    with company_repository.lock(cid):
        row = get_company(cid)
        if row["status"] == "INACTIVE":
            _check_deactivation_reason(reason)
            if reason == "TRANSFERRED" and row["deactivation_reason"] == "MANUAL":
                company_repository.update_company(cid, deactivation_reason="TRANSFERRED")
                company_repository.audit(cid, None, "stepDeactivateCompany", None,
                            {"deactivationReason": ["MANUAL", "TRANSFERRED"],
                             "processId": input.get("processId"),
                             "stepRunId": input.get("stepRunId")})
            return standin.step_reply(input, {"companyId": cid, "status": row["status"],
                                              "deactivationReason": row["deactivation_reason"]})
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        _check_deactivation_reason(reason)
        company_repository.update_company(cid, status="INACTIVE", deactivation_reason=reason,
                             deactivated_at=utc_now())
        company_repository.audit(cid, None, "stepDeactivateCompany", None,
                    {"deactivationReason": reason, "processId": input.get("processId"),
                     "stepRunId": input.get("stepRunId")})
        events.publish(MODULE, "CompanyDeactivated", {"companyId": cid, "reason": reason})
    return standin.step_reply(input, {"companyId": cid, "status": "INACTIVE",
                                      "deactivationReason": reason})


def _check_deactivation_reason(reason) -> None:
    if reason not in company_repository.DEACTIVATION_REASONS:
        raise Problem(MODULE, 400, "validation",
                      errors=[{"field": "reason", "reason": "MANUAL or TRANSFERRED"}],
                      retryable=False)


def deactivate_company_by_staff(companyId: str, body: dict, sub: str | None = None) -> dict:
    """7.13: manual deactivation by OSP staff, always with a justification."""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] == "INACTIVE":
            return company_view(companyId, detail=True)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        errors = company_validation.validate_reason(body.get("reason"))
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)
        company_repository.update_company(companyId, status="INACTIVE", deactivation_reason="MANUAL",
                             deactivated_at=utc_now())
        company_repository.audit(companyId, sub, "deactivateCompany", None, {"reason": body.get("reason")})
        events.publish(MODULE, "CompanyDeactivated", {"companyId": companyId, "reason": "MANUAL"})
    return company_view(companyId, detail=True)


def reactivate_company(input: dict) -> dict:
    """8.6: back to ACTIVE from an approved application of the matching kind."""
    cid, application_id = input.get("companyId"), input.get("applicationId")
    with company_repository.lock(cid):
        row = get_company(cid)
        if row["status"] == "ACTIVE":
            return standin.step_reply(input, {"companyId": cid, "status": row["status"],
                                              "bpn": row["bpn"], "companyRoles": active_roles(cid),
                                              "changedFields": []})
        if row["status"] != "INACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)

        application = _application(application_id)
        if application.get("companyId") != cid:
            raise Problem(MODULE, 409, "conflict", detail="application has another companyId",
                          retryable=False)
        expected = "TRANSFER" if row["deactivation_reason"] == "TRANSFERRED" else "REACTIVATION"
        if application.get("kind") != expected:
            raise Problem(MODULE, 409, "invalid-state",
                          detail=f"kind {application.get('kind')} does not match the reason",
                          retryable=False)
        # C12 calls this step after ApplicationApproved and before complete-application (flows
        # `reactivation` and `return`), so C1-M2 still has the application SUBMITTED; a repetition
        # after the flow may find it COMPLETED. C1-M2's ApplicationStatus has no APPROVED: the
        # approval is C1-M3's (C1-M2 openapi ApplicationStatus; OPEN-QUESTIONS 12).
        if application.get("status") not in ("SUBMITTED", "COMPLETED"):
            raise Problem(MODULE, 409, "invalid-state",
                          detail=f"application {application.get('status')}", retryable=False)

        data = application.get("companyData") or {}
        source_address = data.get("address") or {}
        verification = application.get("verification")
        fields = {"name": data.get("legalName"), "short_name": data.get("shortName"),
                  "street": source_address.get("streetName"),
                  "house_number": source_address.get("streetNumber"),
                  "postal_code": source_address.get("postalCode"), "city": source_address.get("city"),
                  "region": source_address.get("region"),
                  "country_code": source_address.get("countryCode")}
        if verification == "EBW" and company_validation.same_value(row["name"], data.get("legalName")):
            fields["name"] = row["name"]   # 6.3: an equal value keeps its stored spelling
        mismatched = []
        if fields["country_code"] != row["country_code"]:
            mismatched.append("countryCode")
        stored = {entry["type"]: entry for entry in company_repository.list_identifiers(cid)}
        if verification == "EBW":
            claimed_ebwoid = next((entry["value"] for entry in data.get("identifiers") or []
                                   if entry.get("type") == "EBWOID"), None)
            if company_validation.value_normalized(claimed_ebwoid or "") !=\
                    (stored.get("EBWOID") or {}).get("value_normalized"):
                mismatched.append("EBWOID")
        if mismatched:
            raise Problem(MODULE, 409, "company-mismatch", fields=mismatched, retryable=False)

        identifiers = list(stored.values())
        for entry in data.get("identifiers") or []:
            if entry.get("type") == "EBWOID":
                continue
            if verification == "EBW":
                if entry.get("type") not in CORE_IDENTIFIERS:
                    continue
                source = "BUSINESS_WALLET" if (stored.get(entry["type"]) or {}).get("source") == "BUSINESS_WALLET" else "DECLARED"
            else:
                source = "DECLARED" if (stored.get(entry["type"]) or {}).get("source") != "BUSINESS_WALLET" else "BUSINESS_WALLET"
            identifiers = [item for item in identifiers if item["type"] != entry["type"]]
            identifiers.append({"type": entry["type"], "value": entry["value"], "source": source})
        identifiers = [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
                       for entry in identifiers]

        errors = company_validation.validate_company(fields)
        errors += company_validation.validate_identifiers(identifiers, fields["country_code"])
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors, retryable=False)

        attestation_claims = application.get("attestation") or {}
        updates = dict(fields)
        updates |= {"status": "ACTIVE", "deactivation_reason": None, "reactivated_at": utc_now()}
        if verification == "EBW":
            updates |= {"core_data_source": "EBW",
                        "core_data_verified_at": attestation_claims.get("verifiedAt"),
                        "verification_ref": attestation_claims.get("attestationId")}
        else:
            updates |= {"core_data_source": "MANUAL", "core_data_verified_at": utc_now()}
        changed = changed_fields(row, fields, identifiers)
        company_repository.update_company(cid, **updates)
        company_repository.set_identifiers(cid, identifiers)
        company_repository.audit(cid, None, "stepReactivateCompany", None,
                    {"applicationId": application_id, "changedFields": changed,
                     "processId": input.get("processId"), "stepRunId": input.get("stepRunId")})
        if changed:
            events.publish(MODULE, "CompanyDataChanged",
                           {"companyId": cid, "changedFields": changed, "coreDataChanged": True,
                            "coreDataSource": updates["core_data_source"]})
        roles = sorted(role for role, status in company_repository.list_roles(cid).items() if status == "ACTIVE")
        events.publish(MODULE, "CompanyReactivated",
                       {"companyId": cid, "bpn": row["bpn"], "companyRoles": roles})
    return standin.step_reply(input, {"companyId": cid, "status": "ACTIVE", "bpn": row["bpn"],
                                      "companyRoles": roles, "changedFields": changed})

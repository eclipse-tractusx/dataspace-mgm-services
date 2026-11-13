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
"""Company data: changes by people (7.2) and with an attestation (7.3), corrections by OSP staff (7.12),
and the search of OSP staff (7.10).
"""
from __future__ import annotations

from features.company_profile.managers import company_repository
from features.company_profile.services import attestation_verifier, company_validation
from features.company_profile.services.company_changes import (
    CORE_TEXT_FIELDS,
    changed_fields,
    identifier_core_changed,
    identifiers_from,
    validate_merge,
    wallet_identifier_conflict,
)
from features.company_profile.services.company_views import company_view, get_company
from features.company_profile.services.shared import MODULE, parse_timestamp, utc_now
from portal_common import events
from portal_common.problems import Problem


def update_company(companyId: str, body: dict, sub: str | None = None) -> dict:
    """7.2: the Company Admin changes the short name."""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        locked = [key for key in body if company_validation.field_name(key) not in ("short_name",)]
        if locked:
            raise Problem(MODULE, 409, "field-locked", fields=locked)
        errors = company_validation.validate_company(body, partial=True)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)
        changed = changed_fields(row, body, None)
        if not changed:
            return company_view(companyId)
        before = {"short_name": row["short_name"]}
        company_repository.update_company(companyId, short_name=company_validation.flat_fields(body).get("short_name"))
        company_repository.audit(companyId, sub, "updateCompany", None,
                    {"changedFields": changed, "old": before,
                     "new": {key: body.get(key) for key in body}})
        events.publish(MODULE, "CompanyDataChanged",
                       {"companyId": companyId, "changedFields": changed, "coreDataChanged": False,
                        "coreDataSource": row["core_data_source"]})
    return company_view(companyId)


# ----------------------------------------------------------------- correction by OSP staff (7.12)
OSP_LOCKED_FIELDS = {"bpn", "status", "coreDataSource", "applicationId", "verificationRef",
                     "deactivationReason", "createdAt", "changedAt"}


def correct_company(companyId: str, body: dict, sub: str | None = None) -> dict:
    """7.12: correction by OSP staff, always with a justification."""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] in ("REJECTED", "INACTIVE"):
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        errors = company_validation.validate_reason(body.get("reason"))
        identifiers = identifiers_from(body)
        fields = {key: value for key, value in company_validation.flat_fields(body).items()
                  if key not in ("reason", "identifiers")}

        locked = [key for key in fields if key not in CORE_TEXT_FIELDS + ("short_name",)]
        if "country_code" in fields and (row["status"] != "REQUESTED" or row["bpn"]):
            locked.append("countryCode")
        if locked:
            raise Problem(MODULE, 409, "field-locked", fields=locked)

        if identifiers is not None:
            wallet = [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
                      for entry in company_repository.list_identifiers(companyId)
                      if entry["source"] == "BUSINESS_WALLET"]
            errors += company_validation.validate_identifiers(list(identifiers) + wallet, row["country_code"])
            errors += wallet_identifier_conflict(row, identifiers)
        errors += company_validation.validate_company(validate_merge(row, fields), partial=False)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)

        changed = changed_fields(row, fields, identifiers)
        if not changed:
            return company_view(companyId, detail=True)

        core_changed = any(company_validation.field_name(key) in CORE_TEXT_FIELDS for key in fields)
        if identifiers is not None and identifier_core_changed(row, identifiers):
            core_changed = True
        updates = company_validation.flat_fields(fields)
        if core_changed:
            updates["core_data_verified_at"] = utc_now()
            if row["core_data_source"] == "EBW":
                updates["core_data_source"] = "MANUAL"
                updates["verification_ref"] = None
        company_repository.update_company(companyId, **updates)
        if identifiers is not None:
            company_repository.set_identifiers(companyId, identifiers)
        company_repository.audit(companyId, sub, "correctCompany", None,
                    {"changedFields": changed, "reason": body.get("reason"),
                     "old": {field: row.get(field) for field in updates},
                     "new": fields})
        events.publish(MODULE, "CompanyDataChanged",
                       {"companyId": companyId, "changedFields": changed,
                        "coreDataChanged": core_changed,
                        "coreDataSource": updates.get("core_data_source", row["core_data_source"])})
    return company_view(companyId, detail=True)


# ---------------------------------------------------------------------- search for OSP (7.10)
def _summary(row: dict) -> dict:
    return {"id": row["id"], "name": row["name"], "status": row["status"], "bpn": row["bpn"],
            "coreDataSource": row["core_data_source"], "countryCode": row["country_code"],
            "companyRoles": [role for role, status in company_repository.list_roles(row["id"]).items()
                             if status == "ACTIVE"],
            "createdAt": row["created_at"]}


def list_companies(*, status: list[str] | str | None = None, name: str | None = None,
                   bpn: str | None = None, hasBpn: bool | str | None = None,
                   companyRole: str | None = None, coreDataSource: str | None = None,
                   page: int | str = 0, size: int | str = 20) -> dict:
    """7.10: filters, newest first, paged; `companyRole` matches active roles only."""
    has_bpn = None if hasBpn in (None, "") else str(hasBpn).lower() in ("1", "true", "yes")
    try:
        items, total = company_repository.find_companies(
            status=status, name=name, bpn=bpn, has_bpn=has_bpn, company_role=companyRole,
            core_data_source=coreDataSource, page=int(page or 0), size=int(size or 20))
    except ValueError as error:
        raise Problem(MODULE, 400, "validation", errors=[{"field": "filter", "reason": str(error)}])
    return {"items": [_summary(row) for row in items], "page": int(page or 0),
            "size": int(size or 20), "total": total}


# ----------------------------------------------------- change with an attestation (7.3, 6.3, 6.7)
def _attested_values(row: dict, claims: dict) -> tuple[dict, dict[str, dict]]:
    """Name, address and identifiers from the claims (6.3); returns the fields and the identifiers."""
    company = claims.get("company") or {}
    fields = {"name": company.get("legal_name")}
    stored = {entry["type"]: entry for entry in company_repository.list_identifiers(row["id"])}
    identifiers = [{"type": kind, "value": entry["value"], "source": entry["source"]}
                   for kind, entry in stored.items()]
    for entry in identifiers:
        if entry["type"] == "EBWOID":
            if not company_validation.same_value(entry["value"], company.get("ebwoid")):
                entry["value"] = company.get("ebwoid")
            entry["source"] = "BUSINESS_WALLET"
    if not any(entry["type"] == "EBWOID" for entry in identifiers):
        identifiers.append({"type": "EBWOID", "value": company.get("ebwoid"),
                            "source": "BUSINESS_WALLET"})
    if company.get("euid"):
        identifiers = [entry for entry in identifiers if entry["type"] != "EUID"]
        identifiers.append({"type": "EUID", "value": company["euid"], "source": "BUSINESS_WALLET"})

    address = company.get("address")
    if isinstance(address, dict):
        same_street = company_validation.same_value(
            " ".join(filter(None, (row["street"], row["house_number"]))), address.get("street_address"))
        same_city = (company_validation.same_value(row["postal_code"], address.get("postal_code"))
                     and company_validation.same_value(row["city"], address.get("locality")))
        if not (same_street and same_city):
            fields |= {"street": address.get("street_address"), "house_number": None,
                       "address_addition": None, "region": None,
                       "postal_code": address.get("postal_code"), "city": address.get("locality")}
    return fields, {entry["type"]: entry for entry in identifiers}


def update_company_from_attestation(companyId: str, body: dict, sub: str | None = None) -> dict:
    """7.3: core data from a new verification attestation, immediately and without OSP staff."""
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        claims = attestation_verifier.verify(body.get("attestation") or "")
        claims["client_id"] = claims.get("client_id")

        if company_repository.is_used(claims["jti"]):
            raise Problem(MODULE, 409, "attestation-used")
        if claims.get("representation", {}).get("confirmed") is not True:
            raise Problem(MODULE, 409, "representation-not-confirmed")
        company = claims.get("company") or {}
        stored = {entry["type"]: entry for entry in company_repository.list_identifiers(companyId)}
        mismatched = []
        if not company_validation.same_value((stored.get("EBWOID") or {}).get("value"), company.get("ebwoid")):
            mismatched.append("EBWOID")
        if (row["country_code"] or "") != (company.get("country") or ""):
            mismatched.append("countryCode")
        if mismatched:
            raise Problem(MODULE, 409, "company-mismatch", fields=mismatched)
        verified_at = claims["_verified_at"].isoformat()
        stored_verified_at = parse_timestamp(row["core_data_verified_at"])
        if stored_verified_at is not None and claims["_verified_at"] <= stored_verified_at:
            raise Problem(MODULE, 409, "attestation-outdated")

        fields, identifiers = _attested_values(row, claims)
        errors = company_validation.validate_company(fields, partial=True)
        errors += company_validation.validate_identifiers(list(identifiers.values()), row["country_code"])
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)

        changed = changed_fields(row, fields, list(identifiers.values()))
        updates = dict(fields)
        updates |= {"core_data_source": "EBW", "core_data_verified_at": verified_at,
                    "verification_ref": claims["jti"]}
        company_repository.update_company(companyId, **updates)
        company_repository.set_identifiers(companyId, list(identifiers.values()))
        company_repository.add_if_unused(claims["jti"], companyId)
        company_repository.audit(companyId, sub, "updateCompanyFromAttestation", None,
                    {"changedFields": changed, "verificationRef": claims["jti"],
                     "old": {field: row.get(field) for field in
                             ("name", "street", "house_number", "postal_code", "city", "region")},
                     "new": fields})
        if changed:
            events.publish(MODULE, "CompanyDataChanged",
                           {"companyId": companyId, "changedFields": changed,
                            "coreDataChanged": True, "coreDataSource": "EBW"})
    return {"changedFields": changed, "company": company_view(companyId)}

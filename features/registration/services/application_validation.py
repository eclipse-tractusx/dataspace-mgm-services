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
"""Input checks of applications against the reference data (README 6, 7.2).
"""
from __future__ import annotations

import re
import uuid

from features.registration.managers import reference_catalog
from features.registration.services.shared import ATTESTATION_MAX_CHARS, field_error, validation_problem

KINDS = ("ONBOARDING", "REACTIVATION", "TRANSFER")
VERIFICATIONS = ("EBW", "DOCUMENTS")
IDENTIFIER_TYPES = ("EUID", "EBWOID", "COMMERCIAL_REG_NUMBER", "VAT_ID", "LEI_CODE", "EORI")


# ------------------------------------------------------------------------------ input checks
def _check_address(address: object, field: str, errors: list[dict], required: bool = True) -> None:
    if not isinstance(address, dict):
        errors.append(field_error(field, "must be an object"))
        return
    limits = (("streetName", 150, True), ("streetNumber", 20, False), ("postalCode", 12, False), ("city", 150, True))
    for name, maximum, needed in limits:
        value = address.get(name)
        if value in (None, ""):
            if needed and required:
                errors.append(field_error(f"{field}.{name}", "required"))
        elif not isinstance(value, str) or len(value) > maximum:
            errors.append(field_error(f"{field}.{name}", f"text of at most {maximum} characters"))
    region = address.get("region")
    if region not in (None, "") and not (isinstance(region, str) and re.fullmatch(r"[A-Z0-9]{1,3}", region)):
        errors.append(field_error(f"{field}.region", "code of the region, 1 to 3 characters"))
    if not (isinstance(address.get("countryCode"), str) and re.fullmatch(r"[A-Z]{2}", address["countryCode"])):
        errors.append(field_error(f"{field}.countryCode", "ISO 3166-1 alpha-2"))


def _check_identifiers(identifiers: object, errors: list[dict]) -> None:
    if not isinstance(identifiers, list) or len(identifiers) > 10:
        errors.append(field_error("identifiers", "list of at most 10 identifiers"))
        return
    seen = set()
    for i, x in enumerate(identifiers):
        if not isinstance(x, dict) or x.get("type") not in IDENTIFIER_TYPES\
                or not isinstance(x.get("value"), str) or not 1 <= len(x["value"]) <= 200:
            errors.append(field_error(f"identifiers[{i}]", "needs a known type and a value of 1 to 200 characters"))
        elif x["type"] in seen:
            errors.append(field_error(f"identifiers[{i}]", f"at most one identifier per type: {x['type']}"))
        else:
            seen.add(x["type"])


def check_company_fields(data: dict, errors: list[dict]) -> None:
    name = data.get("legalName")
    if name is not None and not (isinstance(name, str) and 1 <= len(name) <= 160 and re.fullmatch(r"\S(.*\S)?", name)):
        errors.append(field_error("legalName", "1 to 160 characters, without whitespace at the start and end"))
    short = data.get("shortName")
    if short is not None and not (isinstance(short, str) and len(short) <= 60):
        errors.append(field_error("shortName", "at most 60 characters"))
    if data.get("address") is not None:
        _check_address(data["address"], "address", errors)
    if data.get("identifiers") is not None:
        _check_identifiers(data["identifiers"], errors)


def check_roles(company_roles: object, errors: list[dict]) -> None:
    if not isinstance(company_roles, list) or not company_roles:
        errors.append(field_error("companyRoles", "at least one company role"))
    elif len(set(map(str, company_roles))) != len(company_roles):
        errors.append(field_error("companyRoles", "without duplicates"))


def _is_uuid(value: object) -> bool:
    try:
        uuid.UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return True


def check_create(body: dict) -> None:
    """7.2 step 2 with the rules of 6.2."""
    errors: list[dict] = []
    kind, verification = body.get("kind"), body.get("verification")
    if kind not in KINDS:
        errors.append(field_error("kind", f"one of {', '.join(KINDS)}"))
    if verification not in VERIFICATIONS:
        errors.append(field_error("verification", f"one of {', '.join(VERIFICATIONS)}"))
    token = body.get("attestation")
    if verification == "EBW" and not (isinstance(token, str) and 0 < len(token) <= ATTESTATION_MAX_CHARS):
        errors.append(field_error("attestation", "required for EBW, at most 16 KB"))
    if verification == "DOCUMENTS" and token is not None:
        errors.append(field_error("attestation", "not allowed for DOCUMENTS"))
    reference = body.get("companyId") or body.get("bpn")
    if body.get("companyId") and body.get("bpn"):
        errors.append(field_error("companyId", "companyId and bpn must not both be given"))
    if body.get("companyId") and not _is_uuid(body["companyId"]):
        errors.append(field_error("companyId", "must be a UUID"))
    if body.get("bpn") and not (isinstance(body["bpn"], str) and re.fullmatch(r"BPNL[A-Z0-9]{12}", body["bpn"])):
        errors.append(field_error("bpn", "must be a BPN"))
    if kind == "ONBOARDING" and reference:
        errors.append(field_error("companyId", "no reference for ONBOARDING"))
    if kind == "REACTIVATION" and not reference:
        errors.append(field_error("companyId", "reference required for REACTIVATION"))
    if body.get("companyRoles") is not None or not reference:
        check_roles(body.get("companyRoles"), errors)
    data = body.get("companyData")
    if data is not None and not isinstance(data, dict):
        errors.append(field_error("companyData", "must be an object"))
    elif data:
        check_company_fields(data, errors)
    if verification == "DOCUMENTS":
        data = data if isinstance(data, dict) else {}
        for name in ("legalName", "address"):
            if not data.get(name):
                errors.append(field_error(f"companyData.{name}", "required for DOCUMENTS"))
        if not data.get("identifiers"):
            errors.append(field_error("companyData.identifiers", "at least one identifier for DOCUMENTS"))
    if errors:
        raise validation_problem(errors)


def check_reference_data(a_data: dict, company_roles: list[str], verification: str) -> None:
    """7.2 step 9: country, identifier types, formats (6.6), selectable roles (6.7)."""
    errors: list[dict] = []
    code = a_data["address"].get("countryCode")
    if reference_catalog.country(code) is None:
        errors.append(field_error("address.countryCode", f"unknown country {code}"))
    else:
        for i, x in enumerate(a_data["identifiers"]):
            if verification == "DOCUMENTS" and x["type"] == "EBWOID":
                errors.append(field_error(f"identifiers[{i}]", "EBWOID is not allowed without a Business Wallet"))
            elif message := reference_catalog.identifier_error(x["type"], x["value"], code):
                errors.append(field_error(f"identifiers[{i}]", message))
    if len(a_data["identifiers"]) > 10:
        errors.append(field_error("identifiers", "at most 10 identifiers"))
    errors += [field_error("companyRoles", f"not selectable: {r}") for r in company_roles if not reference_catalog.selectable(r)]
    if errors:
        raise validation_problem(errors)

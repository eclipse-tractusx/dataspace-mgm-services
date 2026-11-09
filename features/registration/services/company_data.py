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
"""Company data of an application: from the business wallet (EBW) or declared with documents (README 6.3).
"""
from __future__ import annotations

import unicodedata
import uuid

from features.registration.managers import neighbour_client, reference_catalog
from features.registration.managers.application_repository import applications
from features.registration.services.shared import MODULE, field_error, validation_problem
from portal_common.problems import Problem
from tools import testdata


# ------------------------------------------------------------------------------ company data
def _same(a: str, b: str) -> bool:
    """Comparison of 6.5: NFKC, whitespace trimmed and collapsed, case ignored."""
    def norm(s: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", s).split()).casefold()
    return norm(a) == norm(b)


def _compare(field: str, mine: str | None, claim: str | None) -> dict | None:
    if not mine and not claim:
        return None
    if mine and claim:
        return {"field": field, "result": "MATCH" if _same(mine, claim) else "MISMATCH"}
    return {"field": field, "result": "NOT_IN_ATTESTATION" if mine else "FROM_ATTESTATION"}


def given_identifiers(given: dict) -> dict[str, str]:
    return {x["type"]: reference_catalog.normalise_identifier(x["type"], x["value"]) for x in given.get("identifiers") or []}


def company_data_ebw(company: dict, given: dict) -> tuple[dict, list[dict]]:
    """6.5: the attestation is the basis; fixed fields must be equal, compared fields are recorded."""
    ids = given_identifiers(given)
    ebwoid, euid = company["ebwoid"], company.get("euid")
    address, claim = given.get("address"), company.get("address") or {}
    fields = []
    if "EBWOID" in ids and ids["EBWOID"] != ebwoid:
        fields.append("EBWOID")
    if euid and "EUID" in ids and ids["EUID"] != reference_catalog.normalise_identifier("EUID", euid):
        fields.append("EUID")
    if address and address.get("countryCode") != company["country"]:
        fields.append("COUNTRY")
    if fields:
        raise Problem(MODULE, 400, "attestation-mismatch", fields=fields)
    if not address and not (claim.get("street_address") and claim.get("locality")):
        raise validation_problem([field_error("companyData.address", "the attestation has no address: streetName and city required")])
    identifiers = [{"type": "EBWOID", "value": ebwoid, "source": "ATTESTATION"}]
    if euid:
        identifiers.append({"type": "EUID", "value": reference_catalog.normalise_identifier("EUID", euid), "source": "ATTESTATION"})
    identifiers += [{"type": t, "value": v, "source": "APPLICANT"} for t, v in ids.items()
                    if t != "EBWOID" and not (t == "EUID" and euid)]
    street = " ".join(p for p in (address.get("streetName"), address.get("streetNumber")) if p) if address else None
    final = ({**address, "postalCode": address.get("postalCode") or claim.get("postal_code")} if address else
             {"streetName": claim.get("street_address"), "streetNumber": None, "postalCode": claim.get("postal_code"),
              "city": claim.get("locality"), "region": None, "countryCode": company["country"]})
    comparison = [{"field": "EBWOID", "result": "FROM_ATTESTATION"},
                  {"field": "EUID", "result": "FROM_ATTESTATION"} if euid else _compare("EUID", ids.get("EUID"), None),
                  {"field": "COUNTRY", "result": "MATCH" if address else "FROM_ATTESTATION"},
                  _compare("LEGAL_NAME", given.get("legalName"), company["legal_name"]) if given.get("legalName")
                  else {"field": "LEGAL_NAME", "result": "FROM_ATTESTATION"},
                  _compare("STREET", street, claim.get("street_address")),
                  _compare("POSTAL_CODE", address.get("postalCode") if address else None, claim.get("postal_code")),
                  _compare("CITY", address.get("city") if address else None, claim.get("locality"))]
    return ({"legalName": given.get("legalName") or company["legal_name"], "shortName": given.get("shortName"),
             "address": final, "identifiers": identifiers}, [c for c in comparison if c])


def _company_data_documents(given: dict) -> tuple[dict, list[dict]]:
    """6.9: all data from the person."""
    return ({"legalName": given["legalName"], "shortName": given.get("shortName"), "address": given["address"],
             "identifiers": [{"type": t, "value": v, "source": "APPLICANT"} for t, v in given_identifiers(given).items()]}, [])


def build_company_data(verification: str, company: dict | None, given: dict) -> tuple[dict, list[dict]]:
    return company_data_ebw(company, given) if verification == "EBW" else _company_data_documents(given)


def check_existing_identifiers(company: dict, ebwoid: str | None, euid: str | None) -> None:
    """6.2: the company of the application must be the existing one."""
    kept = {i["type"]: i["value"] for i in company.get("identifiers") or []}
    fields = []
    if ebwoid and kept.get("EBWOID") and kept["EBWOID"] != ebwoid:
        fields.append("EBWOID")
    if euid and kept.get("EUID") and reference_catalog.normalise_identifier("EUID", kept["EUID"]) != reference_catalog.normalise_identifier("EUID", euid):
        fields.append("EUID")
    if fields:
        raise Problem(MODULE, 400, "attestation-mismatch", fields=fields)


def company_for_reference(body: dict, kind: str) -> dict:
    """6.2: read the company at C3-M1 and check that status and reason fit the application kind."""
    company = neighbour_client.company_by_id(body["companyId"]) if body.get("companyId") else neighbour_client.company_by_bpn(body["bpn"])
    if company is None:
        raise Problem(MODULE, 409, "company-not-eligible", detail="company unknown")
    transferred = company.get("deactivationReason") == "TRANSFERRED"
    eligible = company.get("status") == "INACTIVE" and (transferred if kind == "TRANSFER" else not transferred)
    if not eligible:
        raise Problem(MODULE, 409, "company-not-eligible", companyStatus=company.get("status"))
    return company


def new_company_id(ebwoid: str | None) -> str:
    """7.2 generates the `companyId`; a test company takes its ID of FRAMEWORK 7a once (OPEN-QUESTIONS 3)."""
    cid = testdata.test_company_id(ebwoid)
    if cid and not any(a["companyId"] == cid for a in applications.values()):
        return cid
    return str(uuid.uuid4())

#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""Queries of C3-M2: the duplicate check at the CSP (README 9) and the status of a company at the CSP (README 7.1)."""
from __future__ import annotations

from typing import Any

from features.csp_connection.managers import csp_client, store
from features.csp_connection.managers.store import Registration
from features.csp_connection.models import errors
from features.csp_connection.models.schemas import CspCompanyMatch, CspRegistration, invalid_fields
from features.csp_connection.services.common import COUNTRY


def find_companies(*, ebwoid: str | None = None, euid: str | None = None, identifier: list[str] | str | None = None,
                   legalName: str | None = None, country: str | None = None) -> list[dict[str, Any]]:  # openapi names
    """Query findCompanies (README 9, 6.2): duplicate check at the CSP; one `CspCompanyMatch` per match."""
    params = _search_params(ebwoid, euid, identifier, legalName, country)
    status, answer = csp_client.call("find-companies", "GET", "/companies", params=params)
    if status == 400:
        raise errors.validation("the CSP rejected the search parameters")
    csp_client.raise_for(status, answer, ok=(200,))
    if not isinstance(answer, list):
        raise errors.upstream_error("the CSP answered without a list")
    if not all(isinstance(m, dict) for m in answer):
        raise errors.upstream_error("the CSP answered a match that is not an object")
    own = csp_client.osp_id()
    matches = [{"bpn": m.get("bpn"), "legalName": m.get("legalName"), "country": m.get("country"),
                "matchedBy": m.get("matchedBy"), "homeOspId": m.get("homeOspId"), "homeOspName": m.get("homeOspName"),
                "homeIsThisOsp": m.get("homeOspId") == own, "memberActive": m.get("memberActive")}
               for m in answer]
    # Every match must be a CspCompanyMatch of README 9 (the router's response model). Checked here,
    # so a CSP answer with a missing or wrong field is 502 upstream-error both in-process and over
    # HTTP, never a 500 from the response check of FastAPI.
    for match in matches:
        if fields := invalid_fields(CspCompanyMatch, match):
            raise errors.upstream_error(f"the CSP answered a match with a missing or invalid {fields}")
    return matches


def _search_params(ebwoid: str | None, euid: str | None, identifier: list[str] | str | None, legal_name: str | None,
                   country: str | None) -> dict[str, Any]:
    """The checked query parameters of `GET /companies` at the CSP (README 9, 11.1)."""
    identifiers = [identifier] if isinstance(identifier, str) else list(identifier or [])
    for value in identifiers:
        kind, _, rest = value.partition(":")
        if not kind or not rest:
            raise errors.validation("identifier must have the form <type>:<value>")
    if country and not COUNTRY.match(country):
        raise errors.validation("country must be two upper-case letters")
    if not (ebwoid or euid or identifiers or (legal_name and country)):
        raise errors.validation("ebwoid, euid, identifier, or legalName with country is required")
    params: dict[str, Any] = {k: v for k, v in (("ebwoid", ebwoid), ("euid", euid), ("legalName", legal_name),
                                                ("country", country)) if v}
    if identifiers:
        params["identifier"] = identifiers
    return params


def registration_view(row: Registration) -> dict[str, str]:
    """A registration as `CspRegistration`; empty fields are left out."""
    return CspRegistration.model_validate(row, from_attributes=True).to_json()


def get_csp_registration(companyId: str) -> dict[str, str]:  # openapi name
    """Operation getCspRegistration (README 7.1); 404 `not-found` without a registration."""
    row = store.get_registration(companyId)
    if row is None or row.status is None:
        raise errors.not_found()
    return registration_view(row)

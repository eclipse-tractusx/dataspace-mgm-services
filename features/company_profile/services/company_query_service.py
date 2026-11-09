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
"""Queries of other services (README 9.1 to 9.4): companies, role catalogue, identifier matches.
"""
from __future__ import annotations

from features.company_profile import config
from features.company_profile.managers import company_repository
from features.company_profile.services import company_validation
from features.company_profile.services.company_views import company_internal
from features.company_profile.services.shared import MODULE
from portal_common.problems import Problem


# --------------------------------------------------------------------------- queries (9.1 - 9.3)
def query_company_role_catalog(*, lang: str | None = None, **_other) -> list[dict]:
    """9.4: role catalogue with descriptions in `lang`; the terms of the roles are at C1-M2 (9.3)."""
    wanted = lang or "en"
    return [{"companyRole": role, "assignableBy": entry.get("assignableBy"),
             "description": config.description(role, wanted),
             "descriptions": entry.get("descriptions") or {}}
            for role, entry in config.role_catalogue().items()]


def query_company(*, companyId: str) -> dict:
    """9.1"""
    return company_internal(companyId)


def query_companies(*, id: list[str] | str | None = None, bpn: list[str] | str | None = None,
                    **_other) -> dict:
    """9.2: exactly one of `id` and `bpn`, 1 to QUERY_MAX_COMPANIES values."""
    ids = [id] if isinstance(id, str) else list(id or [])
    bpns = [bpn] if isinstance(bpn, str) else list(bpn or [])
    if bool(ids) == bool(bpns):
        raise Problem(MODULE, 400, "validation",
                      errors=[{"field": "id,bpn", "reason": "exactly one of both"}])
    if len(ids + bpns) > config.query_max_companies():
        raise Problem(MODULE, 400, "validation",
                      errors=[{"field": "id,bpn", "reason": "too many values"}])
    items, found = [], set()
    for wanted in ids:
        if company_repository.get_company(wanted) is not None:
            items.append(company_internal(wanted))
            found.add(wanted)
    for wanted in bpns:
        rows = company_repository.find_companies(bpn=wanted, size=config.query_max_companies())[0]
        live = [row for row in rows if row["status"] != "REJECTED"] or rows
        for other in live:
            items.append(company_internal(other["id"]))
            found.add(wanted)
    return {"items": items, "notFound": [value for value in ids + bpns if value not in found]}


def find_identifier_matches(*, identifiers: list[dict], name: str | None = None,
                            excludeCompanyId: str | None = None,
                            statuses: list[str] | str | None = None, **_other) -> dict:
    """9.3: local duplicate search; the caller decides whether a match is a duplicate."""
    wanted_statuses = [statuses] if isinstance(statuses, str) else list(statuses or [])
    errors = []
    if not 1 <= len(identifiers) <= 10:
        errors.append({"field": "identifiers", "reason": "1 to 10 entries"})
    for entry in identifiers:
        if entry.get("type") not in (*company_repository.IDENTIFIER_TYPES, "BPN"):
            errors.append({"field": "identifiers.type", "reason": str(entry.get("type"))})
        if not entry.get("value"):
            errors.append({"field": "identifiers.value", "reason": "required"})
    for value in wanted_statuses:
        if value not in company_repository.STATUSES:
            errors.append({"field": "statuses", "reason": value})
    if errors:
        raise Problem(MODULE, 400, "validation", errors=errors)
    if not 1 <= len(identifiers) <= 10:
        raise Problem(MODULE, 400, "validation",
                      errors=[{"field": "identifiers", "reason": "1 to 10 entries"}])
    candidates, page, total = [], 0, None
    while total is None or len(candidates) < total:
        batch, total = company_repository.find_companies(
            status=wanted_statuses or ["REQUESTED", "ACTIVE", "INACTIVE"], page=page, size=100)
        candidates += batch
        if not batch:
            break
        page += 1
    wanted_name = company_validation.normalise(name) if name else None
    matches = []
    for row in candidates:
        if row["id"] == excludeCompanyId:
            continue
        own = {(entry["type"], entry["value_normalized"])
               for entry in company_repository.list_identifiers(row["id"])}
        if row["bpn"]:
            own.add(("BPN", company_validation.value_normalized(row["bpn"])))
        matched = sorted({entry["type"] for entry in identifiers
                          if (entry["type"], company_validation.value_normalized(entry["value"])) in own})
        if wanted_name and company_validation.normalise(row["name"]) == wanted_name:
            matched.append("NAME")
        if matched:
            matches.append({"companyId": row["id"], "name": row["name"], "status": row["status"],
                            "bpn": row["bpn"], "matchedOn": matched})
    matches.sort(key=lambda match: len(match["matchedOn"]), reverse=True)
    return {"matches": matches}

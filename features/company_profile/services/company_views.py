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
"""The JSON views of a company (README 5): own company, OSP detail, internal view, roles.
"""
from __future__ import annotations

from features.company_profile import config
from features.company_profile.managers import company_repository
from features.company_profile.services.shared import MODULE
from portal_common.problems import Problem


# ---------------------------------------------------------------------------------- mapping (5)
def get_company(cid: str | None) -> dict:
    row = company_repository.get_company(cid)
    if row is None:
        raise Problem(MODULE, 404, "not-found", retryable=False)
    return row


def address_view(row: dict) -> dict:
    return {key: row.get(field) for key, field in
            (("street", "street"), ("houseNumber", "house_number"),
             ("addressAddition", "address_addition"), ("postalCode", "postal_code"),
             ("city", "city"), ("region", "region"), ("countryCode", "country_code"))}


def identifiers_view(row: dict) -> list[dict]:
    return [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
            for entry in company_repository.list_identifiers(row["id"])]


def active_roles(company: str | None) -> list[str]:
    return sorted(role for role, status in company_repository.list_roles(company).items() if status == "ACTIVE")


def _roles(row: dict) -> list[dict]:
    return [{"companyRole": role, "status": status}
            for role, status in company_repository.list_roles(row["id"]).items()]


def company_view(cid: str | None, *, detail: bool = False) -> dict:
    """`Company` (7.1) and `CompanyDetail` (7.11) in camelCase, with the dataspace name for people."""
    row = get_company(cid)
    view = {"id": row["id"], "name": row["name"], "shortName": row["short_name"],
            "address": address_view(row), "identifiers": identifiers_view(row),
            "coreDataSource": row["core_data_source"],
            "coreDataVerifiedAt": row["core_data_verified_at"], "bpn": row["bpn"],
            "status": row["status"], "companyRoles": _roles(row),
            "createdAt": row["created_at"], "dataspaceName": config.dataspace_name()}
    if detail:
        view |= {"applicationId": row["application_id"], "verificationRef": row["verification_ref"],
                 "bpnAssignedAt": row["bpn_assigned_at"],
                 "deactivationReason": row["deactivation_reason"],
                 "changedAt": row["changed_at"], "activatedAt": row["activated_at"],
                 "rejectedAt": row["rejected_at"], "deactivatedAt": row["deactivated_at"],
                 "reactivatedAt": row["reactivated_at"],
                 "openChangeRequestId": (company_repository.open_change_request(row["id"]) or {}).get("id")}
    return view


def company_internal(cid: str | None) -> dict:
    """`CompanyInternal` (9.1): address, identifiers, source and active roles for other modules."""
    row = get_company(cid)
    return {"id": row["id"], "name": row["name"], "shortName": row["short_name"],
            "address": {key: row.get(field) for key, field in
                        (("street", "street"), ("houseNumber", "house_number"),
                         ("postalCode", "postal_code"), ("city", "city"),
                         ("region", "region"), ("countryCode", "country_code"))},
            "identifiers": identifiers_view(row), "coreDataSource": row["core_data_source"],
            "status": row["status"], "bpn": row["bpn"],
            "companyRoles": [role for role, status in company_repository.list_roles(row["id"]).items()
                             if status == "ACTIVE"],
            "deactivationReason": row["deactivation_reason"], "createdAt": row["created_at"],
            "activatedAt": row["activated_at"], "deactivatedAt": row["deactivated_at"]}


def role_view(cid: str | None) -> dict:
    """`Company` of the paths for people (7.1, 7.7): roles with status, so a role can read REQUESTED."""
    row = get_company(cid)
    view = company_view(cid)
    view["companyRoles"] = [{"companyRole": role, "status": status}
                            for role, status in company_repository.list_roles(row["id"]).items()]
    return view

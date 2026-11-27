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
"""The views of a company (README 5) as response models: own company, OSP detail, internal view.
"""
from __future__ import annotations

from features.company_profile.managers import company_repository, config
from features.company_profile.models.company import (
    Address,
    AddressInternal,
    Company,
    CompanyDetail,
    CompanyInternal,
    CompanyRoleAssignment,
    Identifier,
)
from features.company_profile.models.value_sets import RoleStatus
from features.company_profile.services.shared import MODULE
from portal_common.problems import Problem


def get_company(cid: str | None) -> dict:
    row = company_repository.get_company(cid)
    if row is None:
        raise Problem(MODULE, 404, "not-found", retryable=False)
    return row


def address_view(row: dict) -> Address:
    return Address.model_validate(row)


def identifiers_view(row: dict) -> list[Identifier]:
    return [Identifier.model_validate(entry) for entry in company_repository.list_identifiers(row["id"])]


def active_roles(company: str | None) -> list[str]:
    return sorted(role for role, status in company_repository.list_roles(company).items()
                  if status == RoleStatus.ACTIVE)


def _active_roles_in_order(company: str) -> list[str]:
    return [role for role, status in company_repository.list_roles(company).items() if status == RoleStatus.ACTIVE]


def _company_fields(row: dict) -> dict:
    """The fields `Company` and `CompanyDetail` share, from the row and its neighbours in the tables."""
    return row | {"address": address_view(row), "identifiers": identifiers_view(row),
                  "company_roles": [CompanyRoleAssignment(company_role=role, status=status)
                                    for role, status in company_repository.list_roles(row["id"]).items()],
                  "dataspace_name": config.dataspace_name()}


def company_view(cid: str | None) -> Company:
    """`Company` (7.1): every role with its status and the dataspace name."""
    return Company.model_validate(_company_fields(get_company(cid)))


def company_detail(cid: str | None) -> CompanyDetail:
    """`CompanyDetail` (7.11): the company with its lifecycle and the open change request, for OSP staff."""
    row = get_company(cid)
    open_request = company_repository.open_change_request(row["id"]) or {}
    return CompanyDetail.model_validate(_company_fields(row) | {"open_change_request_id": open_request.get("id")})


def company_internal(cid: str | None) -> CompanyInternal:
    """`CompanyInternal` (9.1): address, identifiers, source and active roles for other modules."""
    return internal_view(get_company(cid))


def internal_view(row: dict) -> CompanyInternal:
    """`CompanyInternal` of a row already read."""
    return CompanyInternal.model_validate(row | {"address": AddressInternal.model_validate(row),
                                                 "identifiers": identifiers_view(row),
                                                 "company_roles": _active_roles_in_order(row["id"])})

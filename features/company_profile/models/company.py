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
#  Assisted-By: Claude Code (claude-opus-5-5)
"""Response models of a company (README 5, 7.1, 7.10 to 7.12, 9.1 to 9.3).

The views differ on purpose: people see the full address and every role with its status (`Company`), OSP
staff also the lifecycle (`CompanyDetail`), other modules a compact form with the active roles only
(`CompanyInternal`, without `addressAddition`).
"""
from __future__ import annotations

from features.company_profile.models.value_sets import (
    CompanyStatus,
    CoreDataSource,
    DeactivationReason,
    IdentifierSource,
    IdentifierType,
)
from portal_common.models import ApiModel


class AddressInternal(ApiModel):
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    region: str | None = None
    country_code: str | None = None


class Address(AddressInternal):
    address_addition: str | None = None


class Identifier(ApiModel):
    type: IdentifierType
    value: str
    source: IdentifierSource


class CompanyRoleAssignment(ApiModel):
    company_role: str
    status: str


class Company(ApiModel):
    """`Company` (7.1): the own company with every role it has or had."""

    id: str
    name: str | None = None
    short_name: str | None = None
    address: Address
    identifiers: list[Identifier]
    core_data_source: CoreDataSource
    core_data_verified_at: str | None = None
    bpn: str | None = None
    status: CompanyStatus
    company_roles: list[CompanyRoleAssignment]
    created_at: str
    dataspace_name: str | None = None


class CompanyDetail(Company):
    """`CompanyDetail` (7.11): the company with its lifecycle, for OSP staff."""

    application_id: str | None = None
    verification_ref: str | None = None
    bpn_assigned_at: str | None = None
    deactivation_reason: DeactivationReason | None = None
    changed_at: str | None = None
    activated_at: str | None = None
    rejected_at: str | None = None
    deactivated_at: str | None = None
    reactivated_at: str | None = None
    open_change_request_id: str | None = None


class CompanySummary(ApiModel):
    """One hit of the OSP search (7.10), with the active roles."""

    id: str
    name: str | None = None
    status: CompanyStatus
    bpn: str | None = None
    core_data_source: CoreDataSource
    country_code: str | None = None
    company_roles: list[str]
    created_at: str


class CompanyInternal(ApiModel):
    """`CompanyInternal` (9.1) for other modules: active roles only."""

    id: str
    name: str | None = None
    short_name: str | None = None
    address: AddressInternal
    identifiers: list[Identifier]
    core_data_source: CoreDataSource
    status: CompanyStatus
    bpn: str | None = None
    company_roles: list[str]
    deactivation_reason: DeactivationReason | None = None
    created_at: str
    activated_at: str | None = None
    deactivated_at: str | None = None


class CompanyLookupResult(ApiModel):
    """9.2: the companies found and the values nothing was found for."""

    items: list[CompanyInternal]
    not_found: list[str]


class IdentifierMatch(ApiModel):
    company_id: str
    name: str | None = None
    status: CompanyStatus
    bpn: str | None = None
    matched_on: list[str]


class IdentifierMatchResult(ApiModel):
    """9.3: candidates, most matched identifiers first; the caller decides what is a duplicate."""

    matches: list[IdentifierMatch]


class AttestationUpdateResult(ApiModel):
    """7.3: what the attestation changed and the company afterwards."""

    changed_fields: list[str]
    company: Company


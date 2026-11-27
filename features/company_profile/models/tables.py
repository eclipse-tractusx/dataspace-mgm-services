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
"""The tables of the company profile (README 5) in the feature's own database (F17, ADR-0003 decision 6).

SQLModel classes on the feature's own base, so they sit only in this feature's `MetaData`. Field names are the
snake_case columns of README 5; `managers/company_repository.py` is the only code that reads or writes them.

- Columns of a value set are `str` holding the values of `value_sets.py`; the repository checks a value
  against its value set before it writes, so a row holds the plain strings the API returns.
- Timestamps stay ISO 8601 strings, as the API returns them (`2026-11-16T10:00:00.123456+00:00`); they all carry
  the same UTC offset, so they also sort as strings.
- Tables whose rows the API lists in the order they were written (identifiers, roles, change requests,
  documents, audit) have an integer `seq` key; the natural key of README 5 is a unique constraint next to it.
- The partial unique indexes of README 5 (one BPN among companies that are not `REJECTED`, one `OPEN` change
  request per company) are database indexes, so two concurrent writers cannot both win.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, Index, LargeBinary, UniqueConstraint
from sqlmodel import Field, SQLModel

from features.company_profile.models import MODULE
from features.company_profile.models.value_sets import ChangeRequestStatus, CompanyStatus
from portal_common import database

if TYPE_CHECKING:   # the base is built at run time; for the type checker it is a SQLModel
    Table = SQLModel
else:
    Table = database.table_base(MODULE)


class CompanyRow(Table, table=True):
    """`company`: core data, state and the timestamps of the lifecycle."""

    __tablename__ = "company"

    id: str = Field(primary_key=True)
    name: str
    short_name: str | None = None
    street: str
    house_number: str | None = None
    address_addition: str | None = None
    postal_code: str | None = None
    city: str
    region: str | None = None
    country_code: str
    status: str = Field(index=True)
    bpn: str | None = Field(default=None, index=True)
    bpn_assigned_at: str | None = None
    core_data_source: str
    core_data_verified_at: str | None = None
    verification_ref: str | None = None
    application_id: str | None = None
    deactivation_reason: str | None = None
    created_at: str = Field(index=True)
    changed_at: str
    activated_at: str | None = None
    rejected_at: str | None = None
    deactivated_at: str | None = None
    reactivated_at: str | None = None


class IdentifierRow(Table, table=True):
    """`company_identifier`: at most one identifier per type and company (6.4)."""

    __tablename__ = "company_identifier"
    __table_args__ = (UniqueConstraint("company_id", "type"),
                      Index("company_identifier_value_normalized", "type", "value_normalized"))

    seq: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    type: str
    value: str
    value_normalized: str
    source: str
    created_at: str
    changed_at: str


class RoleRow(Table, table=True):
    """`company_role_assignment`: a removed role keeps its row with status `INACTIVE`."""

    __tablename__ = "company_role_assignment"
    __table_args__ = (UniqueConstraint("company_id", "company_role"),)

    seq: int | None = Field(default=None, primary_key=True)
    company_id: str = Field(index=True)
    company_role: str
    status: str
    source_kind: str
    source_ref: str | None = None
    activated_at: str | None = None
    deactivated_at: str | None = None
    changed_at: str


class ConsentRow(Table, table=True):
    """`consent`: one row per company and terms, with the latest state."""

    __tablename__ = "consent"

    company_id: str = Field(primary_key=True)
    agreement_key: str = Field(primary_key=True)
    agreement_version: str | None = None
    status: str
    source_kind: str
    source_ref: str | None = None
    consented_by: str | None = None
    consented_at: str | None = None
    changed_at: str


class ChangeRequestRow(Table, table=True):
    """`change_request`: the requested core data changes and the decision of OSP staff."""

    __tablename__ = "change_request"

    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(unique=True)
    company_id: str = Field(index=True)
    status: str = Field(index=True)
    changes: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    comment: str | None = None
    requested_by: str | None = None
    decided_by: str | None = None
    decision_reason: str | None = None
    created_at: str
    closed_at: str | None = None


class DocumentRow(Table, table=True):
    """`change_request_document`: a supporting document with its checksum."""

    __tablename__ = "change_request_document"

    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(unique=True)
    change_request_id: str = Field(index=True)
    file_name: str
    media_type: str
    size_bytes: int
    sha256: str
    content: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    created_at: str


class UsedAttestationRow(Table, table=True):
    """`used_attestation`: every attestation `jti` is used once (6.7)."""

    __tablename__ = "used_attestation"

    jti: str = Field(primary_key=True)
    company_id: str
    used_at: str


class AuditRow(Table, table=True):
    """`audit_log`: every changing operation, every step and every read of a document (FRAMEWORK 4.3)."""

    __tablename__ = "audit_log"

    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(unique=True)
    occurred_at: str
    sub: str = ""
    company_id: str | None = Field(default=None, index=True)
    operation: str
    object_id: str | None = None
    details: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


# the partial unique indexes of README 5
Index("company_bpn_unique", CompanyRow.bpn, unique=True,
      sqlite_where=CompanyRow.status != CompanyStatus.REJECTED,
      postgresql_where=CompanyRow.status != CompanyStatus.REJECTED)
Index("change_request_open_per_company", ChangeRequestRow.company_id, unique=True,
      sqlite_where=ChangeRequestRow.status == ChangeRequestStatus.OPEN,
      postgresql_where=ChangeRequestRow.status == ChangeRequestStatus.OPEN)

# columns a repository function returns: the README 5 fields without the ordering key
COMPANY_FIELDS = tuple(CompanyRow.model_fields)

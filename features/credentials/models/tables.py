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
#################################################################################
"""Tables of the credentials (README 5) as SQLModel classes in the feature's own database (F17).

Table and column names are those of README 5. Timestamps are timezone-aware UTC `datetime` values in Python on
every database (SQLite keeps no time zone, so `UtcDateTime` stores UTC and gives it back aware).
"""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, DateTime, Dialect, Integer
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel

from features.credentials.models.errors import MODULE
from features.credentials.models.values import CredentialStatus, CredentialType, RevocationReason, Route, RunStatus
from portal_common import database

if TYPE_CHECKING:
    Table = SQLModel                          # what `table_base` returns: a SQLModel class with its own MetaData
else:
    Table = database.table_base(MODULE)


class UtcDateTime(TypeDecorator[dt.datetime]):
    """A timezone-aware UTC timestamp on every database."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(dt.UTC)
        return value

    def process_result_value(self, value: dt.datetime | None, dialect: Dialect) -> dt.datetime | None:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=dt.UTC)
        return value


class CredentialRow(Table, table=True):
    """README 5 `credential`: one row per company and credential type, the state of the last order."""

    __tablename__ = "credential"
    company_id: str = Field(primary_key=True)
    credential_type: CredentialType = Field(primary_key=True)
    id: str = Field(index=True, unique=True)
    status: CredentialStatus = Field(index=True)
    route: Route | None = None
    issuer_did: str | None = None
    wallet_provider: str | None = None
    bpn: str | None = Field(default=None, index=True)
    holder_did: str | None = None
    request_ref: str | None = None
    attempt: int = 0
    requested_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    issued_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    failed_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    revoked_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    failure_reason: str | None = None
    revocation_reason: RevocationReason | None = None
    created_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    changed_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime, index=True)


class IssuanceRunRow(Table, table=True):
    """README 5 `issuance_run`: the last issuance round of a company."""

    __tablename__ = "issuance_run"

    company_id: str = Field(primary_key=True)
    credential_types: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    status: RunStatus
    process_id: str | None = None
    step_run_id: str | None = None
    started_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    finished_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)


class CredentialHistoryRow(Table, table=True):
    """README 5 `credential_history`: every change of a credential row; `seq` keeps the order of writing."""

    __tablename__ = "credential_history"

    seq: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    id: str = Field(index=True)
    credential_id: str = Field(index=True)
    occurred_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    status: CredentialStatus
    attempt: int = 0
    note: str | None = None


class AuditEntryRow(Table, table=True):
    """README 5 `audit_entry`: changing operations over HTTP, identifiers only; `seq` keeps the order."""

    __tablename__ = "audit_entry"

    seq: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True, autoincrement=True))
    id: str = Field(index=True)
    occurred_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    sub: str | None = None
    client_id: str | None = None
    company_id: str | None = None
    operation: str
    object_ref: str | None = None
    result: str | None = None

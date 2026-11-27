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
"""Tables of C4-M2 (README 5) in the feature's own database (`portal_common.database`, F17).

The column names are those of the spec, and the repository (`managers/wallet_store.py`) hands rows to the services
as dicts with exactly these keys. Timestamps are timezone-aware UTC datetimes in Python (`UtcDateTime`).
"""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Column, Dialect, LargeBinary
from sqlalchemy.types import DateTime, TypeDecorator
from sqlmodel import Field, SQLModel

from portal_common import database

from . import MODULE

if TYPE_CHECKING:
    Table = SQLModel    # for the type checker: the base below is a SQLModel class with its own MetaData
else:
    Table = database.table_base(MODULE)


class UtcDateTime(TypeDecorator[dt.datetime]):
    """A timestamp stored as UTC and read back timezone-aware; ISO strings are accepted on write (SQLite keeps no
    time zone, so without this a stored `now()` would come back naive)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: dt.datetime | str | None, dialect: Dialect) -> dt.datetime | None:
        if isinstance(value, str):
            value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(dt.UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: object, dialect: Dialect) -> dt.datetime | None:
        return value.replace(tzinfo=dt.UTC) if isinstance(value, dt.datetime) else None


class WalletRow(Table, table=True):
    """`dataspace_wallet`: one row per company; a new attempt after FAILED reuses it."""

    __tablename__ = "dataspace_wallet"

    company_id: str = Field(primary_key=True)
    id: str = Field(index=True)
    bpn: str | None = Field(default=None, index=True)
    provider: str
    status: str = Field(index=True)
    failure_reason: str | None = None
    did: str | None = Field(default=None, index=True)
    did_document_location: str | None = None
    credential_service_url: str | None = None
    provider_ref: str | None = None
    control_challenge_id: str | None = None
    attempt: int = 1
    provider_ordered_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    validating_since: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    did_validated_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    next_check_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    activated_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    created_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    changed_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)


class WalletSecretRow(Table, table=True):
    """`wallet_secret`: the encrypted holder or STS access of a wallet, one row per kind."""

    __tablename__ = "wallet_secret"

    wallet_id: str = Field(primary_key=True)
    kind: str = Field(primary_key=True)
    url: str
    client_id: str
    secret_encrypted: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    nonce: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    key_version: int
    created_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)


class WalletAccountRow(Table, table=True):
    """`wallet_account`: the access of a technical user to the wallet; `id` is the walletAccountRef."""

    __tablename__ = "wallet_account"

    id: str = Field(primary_key=True)
    technical_user_id: str = Field(index=True)
    company_id: str
    wallet_id: str = Field(index=True)
    provider: str
    status: str = Field(index=True)
    failure_reason: str | None = None
    provider_name: str
    provider_ordered_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    deletion_ordered_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    deletion_failed_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    credentials_state: str
    created_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    changed_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)


class WalletAccountCredentialsRow(Table, table=True):
    """`wallet_account_credentials`: the encrypted secret of an account until it is retrieved once."""

    __tablename__ = "wallet_account_credentials"

    wallet_account_id: str = Field(primary_key=True)
    token_url: str
    client_id: str
    client_secret_encrypted: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    nonce: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    key_version: int
    created_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    expires_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)


class AuditLogRow(Table, table=True):
    """`audit_log`: who did what, without secrets; `seq` keeps the order."""

    __tablename__ = "audit_log"

    seq: int | None = Field(default=None, primary_key=True)
    occurred_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)
    sub: str | None = None
    azp: str | None = None
    company_id: str | None = None
    operation: str
    object_id: str | None = None


class StepLogRow(Table, table=True):
    """`step_log`: every step answer (`RUNNING`, `DONE`) of Process Orchestration; `seq` keeps the order."""

    __tablename__ = "step_log"

    seq: int | None = Field(default=None, primary_key=True)
    step_run_id: str | None = None
    process_id: str | None = None
    step: str
    object_id: str | None = None
    state: str
    occurred_at: dt.datetime | None = Field(default=None, sa_type=UtcDateTime)

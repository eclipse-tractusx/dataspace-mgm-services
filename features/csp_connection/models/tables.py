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
"""The tables of C3-M2 (README 5) as SQLModel classes in the feature's own database (`portal_common.database`).

Column names are those of README 5. Nothing here holds company data beyond the BPN, and the audit log holds no
response content and no tokens (README 5). The value sets of the columns are the Literals of `schemas.py`;
the columns themselves are plain strings, as in the spec's tables.
"""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlmodel import Field, SQLModel

from features.csp_connection.models.errors import MODULE
from portal_common import database

if TYPE_CHECKING:
    Table = SQLModel   # the real base is a subclass of SQLModel created per module at run time
else:
    Table = database.table_base(MODULE)


def now() -> str:
    """Time stamp of a row: UTC, seconds, `Z` (as the API shows it)."""
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class Registration(Table, table=True):
    """`csp_registration`: one company of the installation at the CSP. `status` None: the row exists, but the
    CSP has not answered yet."""
    __tablename__ = "csp_registration"

    company_id: str = Field(primary_key=True)
    bpn: str | None = Field(default=None, index=True)
    status: str | None = Field(default=None, index=True)          # RegistrationStatus (README 6.1)
    failure_reason: str | None = None
    pending_operation_id: str | None = Field(default=None, index=True)
    did: str | None = None
    membership: str = "NONE"                                       # Membership
    registered_at: str | None = None
    updated_at: str = Field(default_factory=now)
    last_update_step_run: str | None = None    # repetition of update-company (OPEN-QUESTIONS 5)
    # a transfer-company back from TRANSFERRED_AWAY is running; `returning` is an SQL keyword, hence the column name
    returning: bool = Field(default=False, sa_column_kwargs={"name": "is_returning"})

    def touch(self) -> None:
        self.updated_at = now()


class Connector(Table, table=True):
    """`csp_connector`: one connector entered in the discovery of the CSP."""
    __tablename__ = "csp_connector"

    connector_id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    bpn: str
    endpoint_url: str
    status: str                                                    # REGISTERED or DEREGISTERED
    registered_at: str
    updated_at: str


class Notification(Table, table=True):
    """`csp_notification`: one accepted notification of the CSP."""
    __tablename__ = "csp_notification"

    notification_id: str = Field(primary_key=True)
    type: str                                                      # NotificationType
    bpn: str | None = None
    received_at: str = Field(default_factory=now)


class AuditEntry(Table, table=True):
    """`audit_entry`: one call to the CSP or one notification. No content, no tokens."""
    __tablename__ = "audit_entry"

    id: int | None = Field(default=None, primary_key=True)        # order of the entries
    time: str = Field(default_factory=now)
    operation: str
    company_id: str | None = None
    bpn: str | None = None
    http_status: int | None = None
    error_type: str | None = None


class EarlyCompletion(Table, table=True):
    """An `OperationCompleted` that arrived before the 202 answer of its operation was stored
    (OPEN-QUESTIONS 15). Applied as soon as the step stores that operation id."""
    __tablename__ = "csp_early_completion"

    id: int | None = Field(default=None, primary_key=True)        # oldest first
    operation_id: str = Field(index=True, unique=True)
    notification_id: str
    outcome: str                                                   # Outcome
    bpn: str | None = None
    reason: str | None = None
    received_at: str = Field(default_factory=now)

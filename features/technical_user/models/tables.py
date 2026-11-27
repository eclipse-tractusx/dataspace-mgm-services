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
"""The tables of the technical users in the feature's own database (F17, README 5 and 6.8).

A row has the fields of its record in `models/__init__.py`, so `row.model_dump()` is the record the services
work on. The logs and the outbox are ordered by `seq`, the order in which they were written."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from portal_common import database

from . import ActorType, Origin, Status, SubscriptionParty, WalletAccess
from .errors import MODULE

if TYPE_CHECKING:   # the type checker sees the base class, the program the feature's own one
    Table = SQLModel
else:
    Table = database.table_base(MODULE)


class TechnicalUserRow(Table, table=True):
    """One technical user; `version` counts the saves (optimistic locking, see the repository)."""

    __tablename__ = "technical_user"

    id: str = Field(primary_key=True)
    company_id: str = Field(index=True)
    name: str
    description: str | None = None
    origin: Origin
    offer_subscription_id: str | None = Field(default=None, index=True)
    subscription_party: SubscriptionParty | None = None
    co_viewer_company_id: str | None = Field(default=None, index=True)
    iam_client_id: str
    iam_client_uuid: str | None = None
    iam_service_account_user_id: str | None = None
    status: Status
    wallet_access: WalletAccess
    wallet_account_ref: str | None = None
    disabled: bool = False
    created_at: str
    changed_at: str
    version: int = 0


class AuditLogRow(Table, table=True):
    """Audit log (README 6.8): who did which operation on which account; no secrets, no names."""

    __tablename__ = "audit_log"

    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(unique=True)
    occurred_at: str
    actor_type: ActorType
    actor_sub: str | None = None
    company_id: str
    process_id: str | None = None
    step_run_id: str | None = None
    operation: str
    object_id: str = Field(index=True)


class RoleAssignmentLogRow(Table, table=True):
    """Role assignment log (README 6.8): every role added to or removed from a client."""

    __tablename__ = "role_assignment_log"

    seq: int | None = Field(default=None, primary_key=True)
    id: str = Field(unique=True)
    occurred_at: str
    technical_user_id: str = Field(index=True)
    company_id: str
    iam_client_id: str
    role_name: str
    action: str
    actor_type: ActorType
    actor_sub: str | None = None
    process_id: str | None = None
    step_run_id: str | None = None
    operation: str


class OutboxRow(Table, table=True):
    """A committed event that is not published yet (README 4: outbox)."""

    __tablename__ = "event_outbox"

    seq: int | None = Field(default=None, primary_key=True)
    event_type: str
    data: dict = Field(sa_column=Column(JSON, nullable=False))


class CounterRow(Table, table=True):
    """A number sequence, e.g. the client IDs `sa1`, `sa2`, ... (6.9); it starts again after `reset()`."""

    __tablename__ = "counter"

    name: str = Field(primary_key=True)
    value: int = 0

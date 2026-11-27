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
"""The tables of C11-M1 (README 5) in the feature's own database (`portal_common.database`).

Each table has an auto-increment `seq` where the order of arrival matters: the inbox is listed in the order the
notifications were stored, and the oldest processed events and dedup keys are dropped first. A row turns into the
model the services use with `StoredNotification.model_validate(row, from_attributes=True)`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from features.notifications.models import MODULE
from portal_common import database

if TYPE_CHECKING:
    Table = SQLModel   # mypy cannot see a class made at run time; the tables are SQLModel tables either way
else:
    Table = database.table_base(MODULE)   # the feature's own registry and MetaData


class NotificationRow(Table, table=True):
    """README 5 `notification`: one notification for one person or one staff permission."""

    __tablename__ = "notification"

    seq: int | None = Field(default=None, primary_key=True)
    notification_id: str = Field(unique=True, index=True)
    source_event_id: str | None = None
    rule: str = Field(index=True)
    type: str
    topic: str
    receiver_sub: str | None = Field(default=None, index=True)
    receiver_permission: str | None = Field(default=None, index=True)
    company_id: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    content: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    for_staff: bool
    done: bool | None = Field(default=None, index=True)
    created_at: str
    done_at: str | None = None


class NotificationStateRow(Table, table=True):
    """README 5 `notification_state`: read and hidden for one person; no row means neither."""

    __tablename__ = "notification_state"

    notification_id: str = Field(primary_key=True)
    sub: str = Field(primary_key=True)
    read_at: str | None = None
    hidden_at: str | None = None


class ApplicantRow(Table, table=True):
    """README 5 `applicant`: the `sub` of the person who submitted the application."""

    __tablename__ = "applicant"

    application_id: str = Field(primary_key=True)
    applicant_sub: str


class ProcessedEventRow(Table, table=True):
    """README 5 `processed_event`: a CloudEvent (`source` and `id`) that was processed, and how it went."""

    __tablename__ = "processed_event"
    __table_args__ = (UniqueConstraint("source", "event_id"),)

    seq: int | None = Field(default=None, primary_key=True)
    source: str
    event_id: str
    type: str | None = None
    received_at: str
    status: str = "DONE"


class DedupKeyRow(Table, table=True):
    """README 5 `dedup_key`: one notification of a rule for one receiver per event, at most once (README 6.4)."""

    __tablename__ = "dedup_key"
    __table_args__ = (UniqueConstraint("rule", "source", "event_id", "receiver"),)

    seq: int | None = Field(default=None, primary_key=True)
    rule: str
    source: str
    event_id: str
    receiver: str

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
"""The tables of Process Orchestration (README 5), as SQLModel classes in the feature's own database.

`process` and `step_run` hold every process with its step runs, `processed_event` the delivered event ids
(README 6.7) and `audit_entry` the retriggers (README 7.4). Nested data of a flow (variables, lookups, the
inbox of events, results, errors, attempts) is JSON. The columns the engine looks up by are indexed: the flow
and correlation value of a new event, the subject of the query of other modules.
"""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from features.process_orchestration.models.errors import MODULE
from portal_common import database

if TYPE_CHECKING:   # the base is built at run time; for the type checker it is a SQLModel
    Table = SQLModel
else:
    Table = database.table_base(MODULE)

Json = dict | list | str | int | float | bool | None   # the value of a JSON column


def _when(*, nullable: bool = True) -> Column:
    """A timestamp column with time zone (every timestamp of the engine is UTC)."""
    return Column(DateTime(timezone=True), nullable=nullable)


class ProcessRow(Table, table=True):
    __tablename__ = "process"

    id: str = Field(primary_key=True)
    sequence: int = Field(index=True)                      # order in which the processes started
    flow_key: str = Field(index=True)
    flow_version: int | None = None
    flow: dict = Field(sa_column=Column(JSON))             # the flow as it was when the process started (README 4)
    subject_type: str = Field(index=True)
    subject_id: str | None = Field(default=None, index=True)          # JSON text of the value
    correlation_key: str
    correlation_value: str | None = Field(default=None, index=True)   # JSON text of the value
    status: str = Field(index=True)
    variables: dict = Field(sa_column=Column(JSON))
    lookups: dict = Field(sa_column=Column(JSON))
    inbox: list = Field(sa_column=Column(JSON))
    trigger_event_id: str | None = None
    end_reason: str | None = None
    created_at: dt.datetime = Field(sa_column=_when(nullable=False))
    updated_at: dt.datetime = Field(sa_column=_when(nullable=False))
    finished_at: dt.datetime | None = Field(default=None, sa_column=_when())


class StepRunRow(Table, table=True):
    __tablename__ = "step_run"

    step_run_id: str = Field(primary_key=True)
    process_id: str = Field(index=True, foreign_key="process.id")
    position: int                                          # order of the step in the flow
    step_key: str
    call: str
    state: str
    attempts: int
    max_attempts: int
    next_attempt_at: dt.datetime | None = Field(default=None, sa_column=_when())
    await_until: dt.datetime | None = Field(default=None, sa_column=_when())
    result: Json = Field(default=None, sa_column=Column(JSON))
    last_error: dict | None = Field(default=None, sa_column=Column(JSON))
    started_at: dt.datetime | None = Field(default=None, sa_column=_when())
    finished_at: dt.datetime | None = Field(default=None, sa_column=_when())
    attempt_history: list = Field(sa_column=Column(JSON))


class ProcessedEventRow(Table, table=True):
    """An event id per engine: an engine that starts empty (after a reset, in a test) has processed nothing yet."""

    __tablename__ = "processed_event"

    engine_id: str = Field(primary_key=True)
    event_id: str = Field(primary_key=True)


class AuditEntryRow(Table, table=True):
    __tablename__ = "audit_entry"

    id: int | None = Field(default=None, primary_key=True)
    at: str
    sub: str
    process_id: str = Field(index=True)
    step_key: str
    comment: str | None = None

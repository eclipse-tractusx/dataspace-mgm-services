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
"""Repository of the processes: the only code that opens the database of Process Orchestration (README 5).

The engine works on live process objects under its lock and hands every changed process to `save()`, which writes
the process and its step runs. The lookups by key go to the indexed columns: the processes of a flow with one
correlation value (README 6.5), the processes of a subject (README 9) and the delivered event ids (README 6.7).
"""
from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from sqlmodel import Session, col, select

from features.process_orchestration.models.errors import MODULE
from features.process_orchestration.models.tables import AuditEntryRow, Json, ProcessedEventRow, ProcessRow, StepRunRow
from portal_common import database

_lock = threading.RLock()


@contextmanager
def _session() -> Iterator[Session]:
    """One unit of work at a time: the default in-memory SQLite database is one connection for all threads, and
    the worker, the event relay and the requests write from different threads."""
    with _lock, database.session(MODULE) as session:
        yield session


def create_tables() -> None:
    with _lock:
        database.create_tables(MODULE)


def reset() -> None:
    with _lock:
        database.reset_tables(MODULE)


def correlation(value: object) -> str:
    """The stored form of a correlation value or subject id: its JSON text, so any JSON value can be indexed."""
    return json.dumps(value, sort_keys=True)


def _plain[T: Json](value: T) -> T:
    """JSON data for a JSON column; a value that JSON does not know (a date of the flow file) as its text.
    The shape stays the same (a dict stays a dict, a list a list)."""
    return cast(T, json.loads(json.dumps(value, default=str)))


def _process_row(proc: dict, sequence: int) -> ProcessRow:
    return ProcessRow(
        id=proc["id"], sequence=sequence, flow_key=proc["flowKey"], flow_version=proc["flowVersion"],
        flow=_plain(proc["flow"]),
        subject_type=proc["subjectType"], subject_id=correlation(proc["subjectId"]),
        correlation_key=proc["correlationKey"], correlation_value=correlation(proc["correlationValue"]),
        status=proc["status"], variables=_plain(proc["variables"]), lookups=_plain(proc["lookups"]),
        inbox=_plain(proc["inbox"]), trigger_event_id=proc["triggerEventId"], end_reason=proc["endReason"],
        created_at=proc["createdAt"], updated_at=proc["updatedAt"], finished_at=proc["finishedAt"])


def _step_row(process_id: str, position: int, sr: dict) -> StepRunRow:
    return StepRunRow(
        step_run_id=sr["stepRunId"], process_id=process_id, position=position, step_key=sr["stepKey"],
        call=sr["call"], state=sr["state"], attempts=sr["attempts"], max_attempts=sr["maxAttempts"],
        next_attempt_at=sr["nextAttemptAt"], await_until=sr["awaitUntil"], result=_plain(sr["result"]),
        last_error=_plain(sr["lastError"]), started_at=sr["startedAt"], finished_at=sr["finishedAt"],
        attempt_history=_plain(sr["attemptHistory"]))


def save(proc: dict, sequence: int) -> None:
    """Writes the process and all its step runs (insert or update); `sequence` orders the processes."""
    with _session() as session:
        session.merge(_process_row(proc, sequence))
        for position, sr in enumerate(proc["steps"]):
            session.merge(_step_row(proc["id"], position, sr))


def ids_of_correlation(flow_key: str, value: object) -> list[str]:
    """Ids of the processes of a flow with this correlation value, in the order they started."""
    with _session() as session:
        return list(session.exec(select(ProcessRow.id).where(ProcessRow.flow_key == flow_key,
                                                             ProcessRow.correlation_value == correlation(value))
                                 .order_by(col(ProcessRow.sequence))))


def ids_of_subject(subject_type: str, subject_id: object) -> list[str]:
    with _session() as session:
        return list(session.exec(select(ProcessRow.id).where(ProcessRow.subject_type == subject_type,
                                                             ProcessRow.subject_id == correlation(subject_id))
                                 .order_by(col(ProcessRow.sequence))))


def record_event(engine_id: str, event_id: str) -> bool:
    """README 6.7: True when the event id is new for this engine (and stores it), False for a repeated delivery."""
    with _session() as session:
        if session.get(ProcessedEventRow, (engine_id, event_id)) is not None:
            return False
        session.add(ProcessedEventRow(engine_id=engine_id, event_id=event_id))
        return True


def add_audit(entry: dict) -> None:
    with _session() as session:
        session.add(AuditEntryRow(at=entry["at"], sub=entry["sub"], process_id=entry["processId"],
                                  step_key=entry["stepKey"], comment=entry["comment"]))

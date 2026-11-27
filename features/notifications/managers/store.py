#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
"""Repository of C11-M1 Notifications (README 5): the tables of `models/tables.py` in the feature's own database.

The only code that opens `database.session(MODULE)`. The services read and write the inbox only through these
functions and get plain data back: a notification is the camelCase dict of `StoredNotification`, a fresh copy on
every read. Three threads use the store (event relay, worker, HTTP requests), so every read-modify-write runs
under `LOCK`; slow work (neighbour calls) never does. Stream events go to `BROKER` (memory, README 7.6).
"""
from __future__ import annotations

import datetime as dt
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlmodel import Session, col, delete, func, or_, select

from features.notifications.models import MODULE
from features.notifications.models.notification import NotificationCreated, NotificationDone, StoredNotification
from features.notifications.models.tables import (
    ApplicantRow,
    DedupKeyRow,
    NotificationRow,
    NotificationStateRow,
    ProcessedEventRow,
)
from portal_common import database, sse, tokens

if TYPE_CHECKING:
    from features.notifications.models.rule import Rule

LOCK = threading.RLock()
SEEN_MAX = 10_000   # events and dedup keys remembered, oldest dropped first (as RECEIVED_MAX of portal_common.events)
BROKER = sse.Broker()                    # README 7.6 stream events of the own inbox
_ready: set[str] = set()                 # database URLs whose tables exist


class Unavailable(Exception):
    """A neighbour (C2-M2, C10-M1) is not reachable; the worker retries the job (README 4)."""


@contextmanager
def _session() -> Iterator[Session]:
    """A unit of work under `LOCK`; the tables are created on first use, also without `on_startup()`."""
    with LOCK:
        if database.url(MODULE) not in _ready:
            create_tables()
        with database.session(MODULE) as session:
            yield session


def create_tables() -> None:
    """Create the tables that do not exist yet (`on_startup()` of the index)."""
    with LOCK:
        database.create_tables(MODULE)
        _ready.add(database.url(MODULE))


def reset() -> None:
    """Empty tables (tests, `/scaffold/reset`)."""
    with LOCK:
        database.reset_tables(MODULE)
        _ready.add(database.url(MODULE))
    BROKER.reset()


def now() -> str:
    """The current time in ISO 8601 UTC (FRAMEWORK 4.1)."""
    return dt.datetime.now(dt.UTC).isoformat()


# ---------------------------------------------------------------- processed events (README 5, 6.4)

def event_key(event: dict) -> tuple[str, str]:
    """The identity of a CloudEvent: `source` and `id` together (FRAMEWORK 6)."""
    return str(event.get("source")), str(event.get("id"))


def first_seen(event: dict) -> bool:
    """README 6.4: record the event as processed; False if it was processed before (at-least-once delivery)."""
    source, event_id = event_key(event)
    with _session() as session:
        if _processed(session, event) is not None:
            return False
        session.add(ProcessedEventRow(source=source, event_id=event_id, type=event.get("type"), received_at=now()))
        _bound(session, ProcessedEventRow)
    return True


def mark_failed(event: dict) -> None:
    """README 5 `processed_event.status`: a part of the event handling failed."""
    with _session() as session:
        row = _processed(session, event)
        if row is not None:
            row.status = "FAILED"
            session.add(row)


def processed_status(event: dict) -> str | None:
    """`DONE` or `FAILED` for a processed event, None if it is not (or no longer) remembered."""
    with _session() as session:
        row = _processed(session, event)
        return row.status if row else None


def processed_events() -> list[tuple[str, str]]:
    """The remembered events as (source, id), oldest first."""
    with _session() as session:
        rows = session.exec(select(ProcessedEventRow).order_by(col(ProcessedEventRow.seq)))
        return [(r.source, r.event_id) for r in rows]


def dedup_keys() -> int:
    """The number of remembered dedup keys."""
    with _session() as session:
        return session.exec(select(func.count()).select_from(DedupKeyRow)).one()


def _processed(session: Session, event: dict) -> ProcessedEventRow | None:
    source, event_id = event_key(event)
    return session.exec(select(ProcessedEventRow).where(ProcessedEventRow.source == source,
                                                        ProcessedEventRow.event_id == event_id)).first()


def _bound(session: Session, table: type[ProcessedEventRow] | type[DedupKeyRow]) -> None:
    """Keep at most `SEEN_MAX` rows of `table`, dropping the oldest (memory and table stay bounded)."""
    session.flush()
    newest = session.exec(select(func.max(col(table.seq)))).one()
    if newest is not None and newest > SEEN_MAX:
        session.exec(delete(table).where(col(table.seq) <= newest - SEEN_MAX))


# ---------------------------------------------------------------- applicants (README 5 `applicant`)

def remember_applicant(application_id: str, applicant_sub: str) -> None:
    with _session() as session:
        session.merge(ApplicantRow(application_id=application_id, applicant_sub=applicant_sub))


def applicant(application_id: str) -> str | None:
    with _session() as session:
        row = session.get(ApplicantRow, application_id)
        return row.applicant_sub if row else None


def forget_applicant(application_id: object) -> None:
    """Drop the row of the application; an `applicationId` that is not an ID raises (the event is marked FAILED)."""
    with _session() as session:
        session.exec(delete(ApplicantRow).where(col(ApplicantRow.application_id) == application_id))


# ---------------------------------------------------------------- notifications (README 5, 6.2)

def add_notification(event: dict, rule: Rule, *, receiver_sub: str | None = None,
                     receiver_permission: str | None = None, done: bool | None = None) -> dict | None:
    """README 6.2: one notification of `rule` for one receiver; `None` if it already exists (6.4).

    Exactly one of `receiver_sub` (personal) and `receiver_permission` (staff) is given. `done` counts
    only for tasks (topic ACTION); for information it is `None`.
    """
    if (receiver_sub is None) == (receiver_permission is None):
        raise ValueError("give exactly one of receiver_sub and receiver_permission")
    data = event.get("data") or {}
    source, event_id = event_key(event)
    receiver = receiver_sub if receiver_sub is not None else f"permission:{receiver_permission}"
    is_task = rule.topic == "ACTION"
    with _session() as session:
        if session.exec(select(DedupKeyRow.seq).where(DedupKeyRow.rule == rule.id, DedupKeyRow.source == source,
                                                       DedupKeyRow.event_id == event_id,
                                                       DedupKeyRow.receiver == receiver)).first() is not None:
            return None
        session.add(DedupKeyRow(rule=rule.id, source=source, event_id=event_id, receiver=receiver))
        _bound(session, DedupKeyRow)
        created = now()   # under the lock, so the inbox stays in `createdAt` order across threads
        row = NotificationRow(
            notification_id=str(uuid.uuid4()), source_event_id=event.get("id"), rule=rule.id,
            type=rule.ntype, topic=rule.topic, receiver_sub=receiver_sub, receiver_permission=receiver_permission,
            company_id=_id(data, rule.company_field), subject_type=rule.subject_type,
            subject_id=_id(data, rule.subject_field), content=dict(data), for_staff=receiver_permission is not None,
            done=bool(done) if is_task else None, created_at=created, done_at=created if is_task and done else None)
        session.add(row)
        session.flush()
        n = _record(row)
    # README 7.6: no content, only IDs, types and states
    BROKER.publish("notification-created", NotificationCreated.model_validate(n).model_dump(mode="json"), _meta(n))
    return n


def close_tasks(rule_id: str, match: Callable[[dict], bool], done_at: str | None = None) -> list[dict]:
    """README 6.2: set `done` on the open tasks of `rule_id` that `match`; publish `notification-done`."""
    rows: list[NotificationRow] = []
    with _session() as session:
        open_tasks = select(NotificationRow).where(NotificationRow.rule == rule_id, NotificationRow.topic == "ACTION",
                                                   col(NotificationRow.done).is_(False)).order_by(col(NotificationRow.seq))
        for row in session.exec(open_tasks):
            if match(_record(row)):
                row.done, row.done_at = True, done_at or now()
                session.add(row)
                rows.append(row)
        session.flush()
        closed = [_record(row) for row in rows]
    for n in closed:
        BROKER.publish("notification-done", NotificationDone.model_validate(n).model_dump(mode="json"), _meta(n))
    return closed


def notifications() -> list[dict]:
    """Every notification, in the order it was stored."""
    with _session() as session:
        return [_record(r) for r in session.exec(select(NotificationRow).order_by(col(NotificationRow.seq)))]


def find(notification_id: str) -> dict | None:
    """The stored notification with this id, or None."""
    with _session() as session:
        row = session.exec(select(NotificationRow).where(NotificationRow.notification_id == notification_id)).first()
        return _record(row) if row else None


def inbox(claims: dict) -> list[dict]:
    """README 4 and 6.3: the caller's personal notifications and the staff ones of the permissions in the token,
    in the order they were stored (one query on the indexed receiver columns)."""
    receivers = [col(NotificationRow.receiver_sub) == claims.get("sub")]
    if permissions := list(tokens.permissions(claims)):
        receivers.append(col(NotificationRow.receiver_permission).in_(permissions))
    with _session() as session:
        return [_record(r) for r in session.exec(select(NotificationRow).where(or_(*receivers))
                                                 .order_by(col(NotificationRow.seq)))]


def visible_to(n: dict, claims: dict) -> bool:
    """README 4 and 6.3: personal notifications of the caller, and staff ones whose permission is in the token."""
    if n["receiverSub"] is not None:
        return n["receiverSub"] == claims.get("sub")
    return n["receiverPermission"] in tokens.permissions(claims)


def stream_visible(meta: dict, claims: dict) -> bool:
    """README 7.6: the same rule for a stream event, from its `meta`."""
    if "sub" in meta:
        return meta["sub"] == claims.get("sub")
    return meta.get("permission") in tokens.permissions(claims)


# ---------------------------------------------------------------- read and hidden per person (README 5)

def states(sub: str | None) -> dict[str, dict]:
    """`notification_state` of one person: notificationId -> {readAt, hiddenAt}, in one query."""
    with _session() as session:
        rows = session.exec(select(NotificationStateRow).where(NotificationStateRow.sub == (sub or "")))
        return {r.notification_id: _state(r) for r in rows}


def state_of(notification_id: str, sub: str | None) -> dict:
    """The row of one person for one notification; empty if they never read or hid it."""
    with _session() as session:
        row = session.get(NotificationStateRow, (notification_id, sub or ""))
        return _state(row) if row else {}


def set_state(notification_id: str, sub: str | None, **fields: str | None) -> None:
    """Set `readAt` and/or `hiddenAt` of the person's row."""
    with _session() as session:
        row = session.get(NotificationStateRow, (notification_id, sub or "")) or \
            NotificationStateRow(notification_id=notification_id, sub=sub or "")
        if "readAt" in fields:
            row.read_at = fields["readAt"]
        if "hiddenAt" in fields:
            row.hidden_at = fields["hiddenAt"]
        session.add(row)


def _state(row: NotificationStateRow) -> dict:
    return {"readAt": row.read_at, "hiddenAt": row.hidden_at}


def _record(row: NotificationRow) -> dict:
    """The row as the camelCase dict the services use."""
    return StoredNotification.model_validate(row, from_attributes=True).model_dump()


def _id(data: dict, field: str | None) -> str | None:
    """An ID field of the event (FRAMEWORK 4.1); a value that is not a string is not stored."""
    value = data.get(field) if field else None
    return value if isinstance(value, str) else None


def _meta(n: dict) -> dict:
    return {"sub": n["receiverSub"]} if n["receiverSub"] is not None else {"permission": n["receiverPermission"]}

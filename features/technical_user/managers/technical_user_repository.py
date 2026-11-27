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
#  The software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#  CONDITIONS OF ANY KIND, either express or implied. See the License for the
#  specific language governing permissions and limitations under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""Persistence of C2-M3 in the feature's own database (F17): technical users, the two logs, the event outbox
and the client ID sequence, as SQLModel tables of `models/tables.py`."""
from __future__ import annotations

import copy
import logging
import threading
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from typing import cast

from sqlalchemy import ColumnElement
from sqlmodel import Session, col, delete, or_, select

from portal_common import database, events

from ..models import AuditLogRecord, RoleAssignmentLogRecord, Status, TechnicalUserRecord
from ..models.errors import MODULE
from ..models.tables import AuditLogRow, CounterRow, OutboxRow, RoleAssignmentLogRow, TechnicalUserRow

log = logging.getLogger("portal.c2-m3")
Publisher = Callable[[str, dict], None]
_CLIENT_NUMBER = "client-id"


def _publish(event_type: str, data: dict) -> None:
    events.publish(MODULE, event_type, data)


class Conflict(RuntimeError):
    """A row was changed by someone else since it was read: the writer must read it again."""


class _KeyLocks:
    """One lock per key, removed again when nobody uses it (no false sharing between different keys)."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, list] = {}   # key -> [lock, number of users]

    @contextmanager
    def hold(self, key: str) -> Iterator[None]:
        with self._guard:
            entry = self._locks.setdefault(key, [threading.RLock(), 0])
            entry[1] += 1
        try:
            with entry[0]:
                yield
        finally:
            with self._guard:
                entry[1] -= 1
                if entry[1] == 0:
                    del self._locks[key]


def _record(row: TechnicalUserRow) -> TechnicalUserRecord:
    return cast(TechnicalUserRecord, row.model_dump())


class TechnicalUserRepository:
    """Persistence contract of C2-M3: rows are values, so change a row and then `save` it.

    `locked(key)` serializes the work on one key; the order of nested keys is company, then subscription, then
    account, and `locked_all` takes several keys at once in a fixed order. `transaction()` makes rows, logs
    and events (`add_event`) one unit of work in the database: the events are written to the outbox table with
    the change and published only after the outermost transaction committed; a failed transaction drops them
    (README 4: outbox), a failed inner transaction only its own (a savepoint). `save` raises `Conflict` for a
    row that changed since it was read. Every read hands out a fresh record, so a missing `save` shows up."""

    def __init__(self, publisher: Publisher = _publish) -> None:
        # one unit of work at a time: the in-memory database has one connection for all threads; never held
        # while a caller does slow work (IAM, neighbours), those run outside of `transaction()`
        self._lock = threading.RLock()
        self._key_locks = _KeyLocks()
        self._publisher = publisher
        self._session: Session | None = None        # of the open transaction, only used under `_lock`
        self._pending: list[tuple[str, dict]] = []   # events of the open transaction

    def reset(self) -> None:
        with self._lock:
            database.reset_tables(MODULE)
            self._pending.clear()

    @contextmanager
    def _unit(self) -> Iterator[Session]:
        """The session of the open transaction, or a unit of work of its own that commits at the end."""
        with self._lock:
            if self._session is not None:
                yield self._session
                return
            with database.session(MODULE) as session:
                yield session

    @contextmanager
    def locked(self, key: str) -> Iterator[None]:
        with self._key_locks.hold(key):
            yield

    @contextmanager
    def locked_all(self, *keys: str) -> Iterator[None]:
        with ExitStack() as stack:
            for key in sorted(set(keys)):   # the same order in every thread: no deadlock
                stack.enter_context(self._key_locks.hold(key))
            yield

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            outermost = self._session is None
            mark = len(self._pending)
            try:
                if outermost:
                    with self._outermost():
                        yield
                else:
                    with cast(Session, self._session).begin_nested():
                        yield
            except BaseException:
                del self._pending[mark:]
                raise
        if outermost:
            self.flush_outbox()

    @contextmanager
    def _outermost(self) -> Iterator[None]:
        with database.session(MODULE) as session:
            self._session = session
            try:
                yield
                session.add_all(OutboxRow(event_type=event_type, data=data) for event_type, data in self._pending)
            finally:
                self._session = None
        self._pending.clear()

    def add_event(self, event_type: str, data: dict) -> None:
        with self._lock:
            if self._session is None:
                raise RuntimeError("an event is added inside the transaction of its change")
            self._pending.append((event_type, copy.deepcopy(data)))

    def flush_outbox(self) -> None:
        """Publishes the committed events in order; one that fails for a temporary reason stays for the next try."""
        with self._lock:
            while (event := self._first_event()) is not None:
                try:
                    self._publisher(event.event_type, event.data)
                except ValueError:   # an invalid event never gets better: report it and go on
                    log.exception("event %s is invalid and was dropped", event.event_type)
                except Exception:
                    log.exception("event %s stays in the outbox", event.event_type)
                    return
                with self._unit() as session:
                    session.execute(delete(OutboxRow).where(col(OutboxRow.seq) == event.seq))

    def _first_event(self) -> OutboxRow | None:
        with self._unit() as session:
            return session.exec(select(OutboxRow).order_by(col(OutboxRow.seq)).limit(1)).first()

    def unsent_events(self) -> list[tuple[str, dict]]:
        with self._unit() as session:
            rows = session.exec(select(OutboxRow).order_by(col(OutboxRow.seq)))
            return [(row.event_type, row.data) for row in rows]

    def next_client_id(self, prefix: str) -> str:
        with self._unit() as session:
            counter = session.get(CounterRow, _CLIENT_NUMBER) or CounterRow(name=_CLIENT_NUMBER)
            counter.value += 1
            session.add(counter)
            return f"{prefix}{counter.value}"

    def save(self, row: TechnicalUserRecord) -> None:
        with self._unit() as session:
            known = session.get(TechnicalUserRow, row["id"])
            if known is not None and known.version != row["version"]:
                raise Conflict(f"technical user {row['id']} changed since it was read")
            if self._party_taken(session, row):
                raise ValueError("a subscription has one account per subscription party")   # README 5: unique
            if known is not None:
                row["version"] += 1
            session.add(known.sqlmodel_update(dict(row)) if known else TechnicalUserRow.model_validate(dict(row)))

    @staticmethod
    def _party_taken(session: Session, row: TechnicalUserRecord) -> bool:
        if not row["subscription_party"] or row["status"] == Status.DELETED:
            return False
        other = select(TechnicalUserRow.id).where(
            TechnicalUserRow.offer_subscription_id == row["offer_subscription_id"],
            TechnicalUserRow.subscription_party == row["subscription_party"],
            TechnicalUserRow.status != Status.DELETED, TechnicalUserRow.id != row["id"])
        return session.exec(other.limit(1)).first() is not None

    def remove(self, user_id: str) -> None:
        with self._unit() as session:
            session.execute(delete(TechnicalUserRow).where(col(TechnicalUserRow.id) == user_id))

    def get(self, user_id: str) -> TechnicalUserRecord | None:
        with self._unit() as session:
            row = session.get(TechnicalUserRow, user_id)
            return _record(row) if row else None

    def find(self, *, owner_company_id: str | None = None, visible_to: str | None = None,
             statuses: tuple[str, ...] | list[str] | None = None, origin: str | None = None,
             wallet_access: str | None = None, disabled: bool | None = None,
             offer_subscription_id: str | None = None) -> list[TechnicalUserRecord]:
        """The rows that match every given filter, in the order they were created."""
        conditions: list[ColumnElement[bool]] = []
        if owner_company_id is not None:
            conditions.append(col(TechnicalUserRow.company_id) == owner_company_id)
        if visible_to is not None:
            conditions.append(or_(TechnicalUserRow.company_id == visible_to,
                                  TechnicalUserRow.co_viewer_company_id == visible_to))
        if statuses is not None:
            conditions.append(col(TechnicalUserRow.status).in_(statuses))
        if origin:
            conditions.append(col(TechnicalUserRow.origin) == origin)
        if wallet_access:
            conditions.append(col(TechnicalUserRow.wallet_access) == wallet_access)
        if disabled is not None:
            conditions.append(col(TechnicalUserRow.disabled) == disabled)
        if offer_subscription_id is not None:
            conditions.append(col(TechnicalUserRow.offer_subscription_id) == offer_subscription_id)
        query = select(TechnicalUserRow).where(*conditions).order_by(col(TechnicalUserRow.created_at),
                                                                     col(TechnicalUserRow.id))
        with self._unit() as session:
            return [_record(row) for row in session.exec(query)]

    def find_subscription(self, subscription_id: str, party: str) -> TechnicalUserRecord | None:
        query = select(TechnicalUserRow).where(TechnicalUserRow.offer_subscription_id == subscription_id,
                                               TechnicalUserRow.subscription_party == party,
                                               TechnicalUserRow.status != Status.DELETED)
        with self._unit() as session:
            row = session.exec(query.limit(1)).first()
            return _record(row) if row else None

    def add_audit_entry(self, entry: AuditLogRecord) -> None:
        with self._unit() as session:
            session.add(AuditLogRow(**entry))

    def add_role_assignment_entry(self, entry: RoleAssignmentLogRecord) -> None:
        with self._unit() as session:
            session.add(RoleAssignmentLogRow(**entry))

    def audit_entries(self) -> list[AuditLogRecord]:
        with self._unit() as session:
            rows = session.exec(select(AuditLogRow).order_by(col(AuditLogRow.seq)))
            return [cast(AuditLogRecord, row.model_dump(exclude={"seq"})) for row in rows]

    def role_assignment_entries(self) -> list[RoleAssignmentLogRecord]:
        with self._unit() as session:
            rows = session.exec(select(RoleAssignmentLogRow).order_by(col(RoleAssignmentLogRow.seq)))
            return [cast(RoleAssignmentLogRecord, row.model_dump(exclude={"seq"})) for row in rows]


repository = TechnicalUserRepository()

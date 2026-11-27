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
"""Repository of the own data of C3-M2 (README 5): the SQLModel tables of `models/tables.py` in the feature's
own database (`portal_common.database`; in-memory SQLite without a database URL).

Services read and change rows only through these functions. A row is returned detached: a service changes
its fields and hands it back with `save()`.

Concurrency: steps run in the worker thread of C12, HTTP requests (the CSP's callbacks) in FastAPI's thread
pool. `lock` serialises every check-then-change of the tables together with the event it publishes, so a
repeated step racing a callback changes a row once and publishes once (FRAMEWORK 4.4). Every function here
takes the lock as well, so a service that holds it reads the rows another thread committed before. Calls to
the CSP are made outside the lock; two concurrent calls of the same step may both call the CSP (its calls are
idempotent), but only the first changes the row and publishes. The audit table keeps the newest `AUDIT_MAX`
entries, the early completions the newest `EARLY_COMPLETIONS_MAX`.
"""
from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, col, delete, func, select

from features.csp_connection.models.errors import MODULE
from features.csp_connection.models.tables import (
    AuditEntry,
    Connector,
    EarlyCompletion,
    Notification,
    Registration,
    now,
)
from portal_common import database, settings

__all__ = [
    "AuditEntry", "Connector", "EarlyCompletion", "Notification", "Registration", "audit_entries",
    "create_tables", "early_completions", "find_by_bpn", "find_by_operation", "get_connector",
    "get_registration", "has_notification", "keep_early_completion", "lock", "now", "pop_early_completion",
    "record_audit", "registered_connectors_of", "registration_row", "registrations", "reset", "save", "seed",
]

EARLY_COMPLETIONS_MAX = 100   # bound, so unknown operation ids from the CSP cannot grow the table without limit
AUDIT_MAX = 10_000            # bound of the audit table (README 5 `audit_entry`), oldest dropped first

lock = threading.RLock()      # see the module docstring: check-then-change of the tables plus its event
_created: set[str] = set()    # database URLs whose tables exist


@contextmanager
def _session() -> Iterator[Session]:
    """A unit of work under `lock`; creates the tables on the first use of a database."""
    with lock:
        if database.url(MODULE) not in _created:
            create_tables()
        with database.session(MODULE) as session:
            yield session


def create_tables() -> None:
    """The tables of README 5 in the feature's database, if they do not exist yet (start-up)."""
    with lock:
        database.create_tables(MODULE)
        _created.add(database.url(MODULE))


def reset() -> None:
    """Empty tables, then the seed data of README 4; a request in flight never sees half-emptied tables."""
    with lock:
        database.reset_tables(MODULE)
        _created.add(database.url(MODULE))
        seed()


def seed() -> None:
    """README 4 "Seed data": the OSP company from `ospCompanyFile` as `REGISTERED`, without a call
    to the CSP and without events. A second run changes nothing."""
    path = settings.resolve_path(settings.get("ospCompanyFile"))
    if path is None or not path.exists():
        return
    company: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(company, dict):
        return
    company_id, bpn = company.get("companyId"), company.get("bpn")
    if not isinstance(company_id, str) or not isinstance(bpn, str):
        return
    with _session() as session:
        if session.get(Registration, company_id) is None:
            stamp = now()
            session.add(Registration(company_id=company_id, bpn=bpn, status="REGISTERED", membership="REGISTERED",
                                     registered_at=stamp, updated_at=stamp))


def save(*rows: SQLModel) -> None:
    """Store changed or new rows."""
    with _session() as session:
        for row in rows:
            session.merge(row)


# ---------------------------------------------------------------- csp_registration
def get_registration(company_id: str) -> Registration | None:
    with _session() as session:
        return session.get(Registration, company_id)


def registrations() -> list[Registration]:
    with _session() as session:
        return list(session.exec(select(Registration)))


def registration_row(company_id: str) -> Registration:
    """The row of the company; created (without status) if there is none yet."""
    with _session() as session:
        row = session.get(Registration, company_id)
        if row is None:
            row = Registration(company_id=company_id)
            session.add(row)
        return row


def find_by_operation(operation_id: str) -> Registration | None:
    with _session() as session:
        return session.exec(select(Registration).where(Registration.pending_operation_id == operation_id)).first()


def find_by_bpn(bpn: str, *, exclude: str | None = None, status: str | None = None) -> Registration | None:
    """A registration with this BPN, optionally of another company or in one status."""
    query = select(Registration).where(Registration.bpn == bpn)
    if exclude is not None:
        query = query.where(Registration.company_id != exclude)
    if status is not None:
        query = query.where(Registration.status == status)
    with _session() as session:
        return session.exec(query.order_by(Registration.company_id)).first()


# ---------------------------------------------------------------- csp_connector
def get_connector(connector_id: str) -> Connector | None:
    with _session() as session:
        return session.get(Connector, connector_id)


def registered_connectors_of(company_id: str) -> list[Connector]:
    with _session() as session:
        return list(session.exec(select(Connector).where(Connector.company_id == company_id,
                                                         Connector.status == "REGISTERED")))


# ---------------------------------------------------------------- csp_notification
def has_notification(notification_id: str) -> bool:
    with _session() as session:
        return session.get(Notification, notification_id) is not None


# ---------------------------------------------------------------- early completions (OPEN-QUESTIONS 15)
def keep_early_completion(early: EarlyCompletion) -> None:
    """Remember a completion for an operation id that is not known yet; drops the oldest beyond the bound."""
    with _session() as session:
        session.exec(delete(EarlyCompletion).where(col(EarlyCompletion.operation_id) == early.operation_id))
        session.add(early)
        session.flush()
        _keep_newest(session, EarlyCompletion, EARLY_COMPLETIONS_MAX)


def pop_early_completion(operation_id: str) -> EarlyCompletion | None:
    with _session() as session:
        early = session.exec(select(EarlyCompletion).where(EarlyCompletion.operation_id == operation_id)).first()
        if early is not None:
            session.delete(early)
        return early


def early_completions() -> list[EarlyCompletion]:
    with _session() as session:
        return list(session.exec(select(EarlyCompletion).order_by(col(EarlyCompletion.id))))


# ---------------------------------------------------------------- audit_entry
def record_audit(operation: str, company_id: str | None, bpn: str | None, http_status: int | None,
                 error_type: str | None = None) -> None:
    """One `audit_entry` (README 5): only status and error type, never the body or a token."""
    with _session() as session:
        session.add(AuditEntry(operation=operation, company_id=company_id, bpn=bpn, http_status=http_status,
                               error_type=error_type))
        session.flush()
        _keep_newest(session, AuditEntry, AUDIT_MAX)


def audit_entries() -> list[AuditEntry]:
    with _session() as session:
        return list(session.exec(select(AuditEntry).order_by(col(AuditEntry.id))))


def _keep_newest(session: Session, table: type[AuditEntry] | type[EarlyCompletion], limit: int) -> None:
    """Drop the oldest rows beyond `limit` (by `id`): one count, and one delete only when over the bound."""
    count = session.exec(select(func.count()).select_from(table)).one()
    if count > limit:
        oldest = select(table.id).order_by(col(table.id)).limit(count - limit)
        session.exec(delete(table).where(col(table.id).in_(oldest)))

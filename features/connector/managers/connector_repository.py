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
"""The register of the connectors (README 5) and the audit log (FRAMEWORK 4.3) in the feature's own database
(`portal_common.database`: `CONNECTOR_DATABASE_URL`, `C6_M1_DATABASE_URL`, `DATABASE_URL`, else in-memory SQLite).
The only code that opens a session of C6-M1.

`LOCK` makes the uniqueness checks of README 5 and the change that follows them one unit, so that of two
concurrent requests the second sees the first (409, OPEN-QUESTIONS.md 12). Every function here takes it, so the
in-memory SQLite connection is never used by two threads at once.
"""
from __future__ import annotations

import datetime as dt
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, col, func, or_, select

from portal_common import database

from ..models import CONNECTOR_AS_A_SERVICE, INACTIVE, MODULE
from ..models.tables import AuditEntryRow, ConnectorRow, DeletedTechnicalUserRow, EndedSubscriptionRow

LOCK = threading.RLock()
_created: set[str] = set()   # database URLs whose tables exist


def create_tables() -> None:
    with LOCK:
        database.create_tables(MODULE)
        _created.add(database.url(MODULE))


def reset() -> None:
    with LOCK:
        database.reset_tables(MODULE)
        _created.add(database.url(MODULE))


@contextmanager
def _session() -> Iterator[Session]:
    with LOCK:
        if database.url(MODULE) not in _created:
            create_tables()
        with database.session(MODULE) as session:
            yield session


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- connectors
def get(connector_id: str) -> ConnectorRow | None:
    with _session() as session:
        return session.get(ConnectorRow, connector_id)


def add(row: ConnectorRow) -> ConnectorRow:
    with _session() as session:
        session.add(row)
    return row


def update(connector_id: str, **changes: object) -> ConnectorRow:
    """Changes the columns of one row and sets `changed_at`."""
    with _session() as session:
        row = session.get(ConnectorRow, connector_id)
        if row is None:
            raise KeyError(connector_id)
        for name, value in (changes | {"changed_at": now()}).items():
            setattr(row, name, value)
        session.add(row)
    return row


def delete(connector_id: str) -> None:
    with _session() as session:
        session.delete(session.get(ConnectorRow, connector_id))


def live_exists(*, ignore: str | None = None, **columns: object) -> bool:
    """Is there a connector that is not `INACTIVE` with these column values (uniqueness of README 5)?"""
    query = select(ConnectorRow.connector_id).where(ConnectorRow.status != INACTIVE)
    for name, value in columns.items():
        query = query.where(getattr(ConnectorRow, name) == value)
    if ignore:
        query = query.where(ConnectorRow.connector_id != ignore)
    with _session() as session:
        return session.exec(query.limit(1)).first() is not None


def find(**columns: object) -> list[ConnectorRow]:
    """The connectors with these column values, oldest first."""
    query = select(ConnectorRow)
    for name, value in columns.items():
        query = query.where(getattr(ConnectorRow, name) == value)
    with _session() as session:
        return list(session.exec(query.order_by(ConnectorRow.created_at, ConnectorRow.connector_id)))


def page_of_company(company_id: str, *, role: str | None, type: str | None, status: str | None,
                    page: int, size: int) -> tuple[list[ConnectorRow], int]:
    """7.1: the connectors the company runs (`provider`) or that a provider runs for it (`host`), without
    `INACTIVE` unless asked; one page in the order of registration, and the total."""
    as_provider = ConnectorRow.provider_company_id == company_id
    as_host = ((ConnectorRow.host_company_id == company_id) & (ConnectorRow.type == CONNECTOR_AS_A_SERVICE)
               & (ConnectorRow.provider_company_id != company_id))
    visible = {"provider": as_provider, "host": as_host}.get(role or "", or_(as_provider, as_host))
    conditions = [visible, ConnectorRow.status == status if status else ConnectorRow.status != INACTIVE]
    if type:
        conditions.append(ConnectorRow.type == type)
    with _session() as session:
        total = session.exec(select(func.count()).select_from(ConnectorRow).where(*conditions)).one()
        rows = session.exec(select(ConnectorRow).where(*conditions)
                            .order_by(ConnectorRow.created_at, ConnectorRow.connector_id)
                            .offset(page * size).limit(size))
        return list(rows), total


def all_connectors() -> list[ConnectorRow]:
    return find()


# ---------------------------------------------------------------- steps 8.1 and 8.2
def mark_subscription_ended(offer_subscription_id: str) -> None:
    with _session() as session:
        session.merge(EndedSubscriptionRow(offer_subscription_id=offer_subscription_id))


def subscription_ended(offer_subscription_id: str) -> bool:
    with _session() as session:
        return session.get(EndedSubscriptionRow, offer_subscription_id) is not None


def mark_technical_user_deleted(technical_user_id: str) -> None:
    with _session() as session:
        session.merge(DeletedTechnicalUserRow(technical_user_id=technical_user_id))


def technical_user_deleted(technical_user_id: str) -> bool:
    with _session() as session:
        return session.get(DeletedTechnicalUserRow, technical_user_id) is not None


# ---------------------------------------------------------------- audit log
def write_audit(operation: str, object_id: str, sub: str | None = None, company_id: str | None = None) -> None:
    """FRAMEWORK 4.3: time, acting person, company, operation, object. No secrets, no names."""
    with _session() as session:
        session.add(AuditEntryRow(at=now(), sub=sub, company_id=company_id, operation=operation, object_id=object_id))


def audit_entries() -> list[AuditEntryRow]:
    with _session() as session:
        return list(session.exec(select(AuditEntryRow).order_by(col(AuditEntryRow.id))))

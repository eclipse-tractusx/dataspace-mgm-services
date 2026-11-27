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
#  Assisted-By: Claude Code (claude-sonnet-5-5)
#################################################################################
"""Storage of the credentials (README 5): the `CredentialStore` contract and its SQLModel repository.

`CredentialStore` is the only thing the services talk to (through `store()`). `SqlCredentialStore` keeps the rows
in the tables of `models/tables.py`, in the feature's own database (`portal_common.database`: the variables
`CREDENTIALS_DATABASE_URL`, `C4_M1_DATABASE_URL`, `DATABASE_URL`, else a private in-memory SQLite database).
It is the only code that opens a session of that database. `transaction(company_id)` is the single place for the
per-company lock of README 6.6.

Rows are plain dicts with the column names of README 5. Timestamps are timezone-aware `datetime` objects; `dump()`
turns them into ISO strings. Rows returned by the store are copies: a change reaches the store only through a
`put_*` call.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import threading
from collections.abc import Iterator, Sequence
from typing import Protocol

from sqlalchemy import ColumnElement
from sqlmodel import Session, SQLModel, col, func, select

from features.credentials.models.errors import MODULE
from features.credentials.models.tables import AuditEntryRow, CredentialHistoryRow, CredentialRow, IssuanceRunRow
from portal_common import database


class CredentialStore(Protocol):
    """Contract of the storage of C4-M1 (TEAM3-PLAN 12.3)."""

    def get_credential(self, company_id: str, credential_type: str) -> dict | None: ...

    def get_credential_by_id(self, credential_id: str) -> dict | None: ...

    def find_credential(self, bpn: str, credential_type: str) -> dict | None: ...

    def put_credential(self, row: dict) -> None: ...

    def list_credentials(self, company_id: str | None = None, statuses: Sequence[str] | None = None,
                         credential_type: str | None = None, route: str | None = None,
                         requested_before: dt.datetime | None = None, page: int = 0,
                         size: int = 50) -> list[dict]: ...

    def count_credentials(self, company_id: str | None = None, statuses: Sequence[str] | None = None,
                          credential_type: str | None = None, route: str | None = None,
                          requested_before: dt.datetime | None = None) -> int: ...

    def get_run(self, company_id: str) -> dict | None: ...

    def put_run(self, run: dict) -> None: ...

    def append_history(self, entry: dict) -> None: ...

    def list_history(self, credential_id: str) -> list[dict]: ...

    def append_audit(self, entry: dict) -> None: ...

    def list_audit(self) -> list[dict]: ...

    def transaction(self, company_id: str) -> contextlib.AbstractContextManager[None]: ...

    def dump(self) -> dict: ...

    def reset(self) -> None: ...


def _jsonable(value: object) -> object:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _as_dict(row: SQLModel) -> dict:
    """A table row as the plain dict the services use (README 5 column names, without the write order `seq`)."""
    return row.model_dump(exclude={"seq"})


def _maybe_dict(row: SQLModel | None) -> dict | None:
    return None if row is None else _as_dict(row)


def _fields(table: type[SQLModel], data: dict) -> dict:
    return {name: data.get(name) for name in table.model_fields if name != "seq" and name in data}


class SqlCredentialStore:
    """`CredentialStore` on the SQLModel tables of the feature's own database."""

    def __init__(self) -> None:
        self._data = threading.RLock()                     # one unit of work at a time on the shared connection
        self._lock_table = threading.Lock()                # guards `_locks`
        self._locks: dict[str, threading.RLock] = {}
        self._ready: set[str] = set()                      # database URLs whose tables exist

    @contextlib.contextmanager
    def _session(self) -> Iterator[Session]:
        with self._data:
            url = database.url(MODULE)
            if url not in self._ready:
                database.create_tables(MODULE)
                self._ready.add(url)
            with database.session(MODULE) as session:
                yield session

    # --- credential ---------------------------------------------------------------------------
    def get_credential(self, company_id: str, credential_type: str) -> dict | None:
        with self._session() as s:
            return _maybe_dict(s.get(CredentialRow, (company_id, credential_type)))

    def get_credential_by_id(self, credential_id: str) -> dict | None:
        with self._session() as s:
            return _maybe_dict(s.exec(select(CredentialRow).where(CredentialRow.id == credential_id)).first())

    def find_credential(self, bpn: str, credential_type: str) -> dict | None:
        """README 5 index (`bpn`, `credential_type`); the BPN is compared in upper case (7.4 step 3)."""
        query = select(CredentialRow).where(CredentialRow.bpn == (bpn or "").upper(),
                                            CredentialRow.credential_type == credential_type)
        with self._session() as s:
            return _maybe_dict(s.exec(query).first())

    def put_credential(self, row: dict) -> None:
        """One row per (`company_id`, `credential_type`): a put replaces the row of the key. The BPN is stored
        in upper case (README 5)."""
        data = _fields(CredentialRow, row)
        if data.get("bpn"):
            data["bpn"] = data["bpn"].upper()
        with self._session() as s:
            s.merge(CredentialRow(**data))

    @staticmethod
    def _filters(company_id: str | None, statuses: Sequence[str] | None, credential_type: str | None,
                 route: str | None, requested_before: dt.datetime | None) -> list[ColumnElement[bool]]:
        """The WHERE conditions of README 7.2; an empty or absent filter matches everything."""
        conditions: list[ColumnElement[bool]] = []
        if company_id:
            conditions.append(col(CredentialRow.company_id) == company_id)
        if statuses:
            conditions.append(col(CredentialRow.status).in_(statuses))
        if credential_type:
            conditions.append(col(CredentialRow.credential_type) == credential_type)
        if route:
            conditions.append(col(CredentialRow.route) == route)
        if requested_before is not None:
            conditions += [col(CredentialRow.requested_at).is_not(None),
                           col(CredentialRow.requested_at) < requested_before]
        return conditions

    def list_credentials(self, company_id: str | None = None, statuses: Sequence[str] | None = None,
                         credential_type: str | None = None, route: str | None = None,
                         requested_before: dt.datetime | None = None, page: int = 0,
                         size: int = 50) -> list[dict]:
        """README 7.2: sorted by `changedAt` descending, one page."""
        where = self._filters(company_id, statuses, credential_type, route, requested_before)
        query = (select(CredentialRow).where(*where).order_by(col(CredentialRow.changed_at).desc())
                 .offset(page * size).limit(size))
        with self._session() as s:
            return [_as_dict(r) for r in s.exec(query)]

    def count_credentials(self, company_id: str | None = None, statuses: Sequence[str] | None = None,
                          credential_type: str | None = None, route: str | None = None,
                          requested_before: dt.datetime | None = None) -> int:
        where = self._filters(company_id, statuses, credential_type, route, requested_before)
        query = select(func.count()).select_from(CredentialRow).where(*where)
        with self._session() as s:
            return s.exec(query).one()

    # --- issuance_run -------------------------------------------------------------------------
    def get_run(self, company_id: str) -> dict | None:
        with self._session() as s:
            run = _maybe_dict(s.get(IssuanceRunRow, company_id))
        if run is not None:
            run["credential_types"] = list(run["credential_types"])
        return run

    def put_run(self, run: dict) -> None:
        data = _fields(IssuanceRunRow, run)
        data["credential_types"] = [str(t) for t in data.get("credential_types") or []]
        with self._session() as s:
            s.merge(IssuanceRunRow(**data))

    # --- credential_history, audit_entry ------------------------------------------------------
    def append_history(self, entry: dict) -> None:
        with self._session() as s:
            s.add(CredentialHistoryRow(**_fields(CredentialHistoryRow, entry)))

    def list_history(self, credential_id: str) -> list[dict]:
        query = (select(CredentialHistoryRow).where(CredentialHistoryRow.credential_id == credential_id)
                 .order_by(col(CredentialHistoryRow.seq)))
        with self._session() as s:
            return [_as_dict(r) for r in s.exec(query)]

    def append_audit(self, entry: dict) -> None:
        with self._session() as s:
            s.add(AuditEntryRow(**_fields(AuditEntryRow, entry)))

    def list_audit(self) -> list[dict]:
        with self._session() as s:
            return [_as_dict(r) for r in s.exec(select(AuditEntryRow).order_by(col(AuditEntryRow.seq)))]

    # --- transaction --------------------------------------------------------------------------
    @contextlib.contextmanager
    def transaction(self, company_id: str) -> Iterator[None]:
        """Steps and status reports of one company run one after the other (README 6.6, stands in for the
        PostgreSQL advisory lock). Re-entrant, so that a step may call the code path of a status report."""
        with self._lock_table:
            lock = self._locks.setdefault(company_id, threading.RLock())
        with lock:
            yield

    # --- test support -------------------------------------------------------------------------
    def dump(self) -> dict:
        """The whole state as JSON-serialisable data (for secret scans in tests)."""
        tables: dict[str, type[SQLModel]] = {"credential": CredentialRow, "issuance_run": IssuanceRunRow,
                                             "credential_history": CredentialHistoryRow, "audit_entry": AuditEntryRow}
        with self._session() as s:
            return {name: [_jsonable(_as_dict(r)) for r in s.exec(select(table))] for name, table in tables.items()}

    def reset(self) -> None:
        """Empties all tables. The locks stay, so that a transaction that is still open stays valid."""
        with self._data:
            database.reset_tables(MODULE)
            self._ready.add(database.url(MODULE))


_store: CredentialStore | None = None


def store() -> CredentialStore:
    """The active `CredentialStore` of the process."""
    global _store
    if _store is None:
        _store = SqlCredentialStore()
    return _store

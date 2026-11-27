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
"""Storage of C4-M2 behind one interface (README 5, 12.2): the repository of the feature's tables.

`WalletStore` is the contract; `DatabaseStore` keeps the rows in the feature's own database (`models/tables.py`,
`portal_common.database`; in-memory SQLite without a database URL). It is the only code that opens a database
session. Rows go in and out as dicts with the column names of the spec tables `dataspace_wallet`,
`wallet_secret`, `audit_log`, `step_log`, `wallet_account` and `wallet_account_credentials`; they are detached
copies, so a caller changes stored state only through `put_*`. Only ciphertext reaches the store; `dump()` shows
bytes as hex.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import threading
from collections.abc import Iterator
from typing import Protocol

from sqlalchemy import ColumnElement
from sqlmodel import Session, SQLModel, col, delete, select

from portal_common import database

from ..models import MODULE
from ..models.tables import (
    AuditLogRow,
    StepLogRow,
    WalletAccountCredentialsRow,
    WalletAccountRow,
    WalletRow,
    WalletSecretRow,
)

# One connection serves the in-memory database of a process: every unit of work holds this lock.
_DATA = threading.RLock()
_LOGS = (AuditLogRow, StepLogRow)
_EARLIEST = dt.datetime.min.replace(tzinfo=dt.UTC)
_DUMP: dict[str, type[SQLModel]] = {
    "dataspace_wallet": WalletRow, "wallet_secret": WalletSecretRow, "audit_log": AuditLogRow, "step_log": StepLogRow,
    "wallet_account": WalletAccountRow, "wallet_account_credentials": WalletAccountCredentialsRow}


class WalletStore(Protocol):
    """Contract of the storage of C4-M2 (TEAM3 plan 12.2)."""

    # wallets (`dataspace_wallet`)
    def get_wallet(self, company_id: str) -> dict | None: ...
    def put_wallet(self, wallet: dict) -> None: ...
    def find_wallet_by_bpn(self, bpn: str) -> dict | None: ...
    def find_wallet_by_did(self, did: str) -> dict | None: ...
    def list_wallets(self, statuses: list[str] | None = None) -> list[dict]: ...

    # secrets (`wallet_secret`)
    def put_secret(self, wallet_id: str, kind: str, url: str, client_id: str, secret_encrypted: bytes,
                   nonce: bytes, key_version: int) -> None: ...
    def get_secret(self, wallet_id: str, kind: str) -> dict | None: ...
    def delete_secrets(self, wallet_id: str) -> None: ...

    # wallet accounts (`wallet_account`, `wallet_account_credentials`)
    def get_account(self, technical_user_id: str) -> dict | None: ...
    def get_account_by_ref(self, wallet_account_ref: str) -> dict | None: ...
    def put_account(self, account: dict) -> None: ...
    def list_accounts(self, wallet_id: str | None = None, statuses: list[str] | None = None) -> list[dict]: ...
    def put_account_credentials(self, wallet_account_id: str, token_url: str, client_id: str,
                                client_secret_encrypted: bytes, nonce: bytes, key_version: int,
                                created_at: dt.datetime | str, expires_at: dt.datetime | str) -> None: ...
    def get_account_credentials(self, wallet_account_id: str) -> dict | None: ...
    def delete_account_credentials(self, wallet_account_id: str) -> None: ...
    def pop_account_credentials(self, wallet_account_id: str) -> dict | None: ...

    # audit log and step log
    def append_audit(self, entry: dict) -> None: ...
    def list_audit(self) -> list[dict]: ...
    def append_step_log(self, entry: dict) -> None: ...
    def list_step_log(self) -> list[dict]: ...

    # one writer per company at a time (README 6.9)
    def transaction(self, company_id: str) -> contextlib.AbstractContextManager: ...

    def dump(self) -> dict: ...
    def reset(self) -> None: ...


def _jsonable(value: object) -> object:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _row(row: SQLModel) -> dict:
    """A row as a detached dict of its spec columns (the log tables without their sequence number)."""
    return row.model_dump(exclude={"seq"} if isinstance(row, _LOGS) else None)


def _plain(row: SQLModel | None) -> dict | None:
    return None if row is None else _row(row)


@contextlib.contextmanager
def _session() -> Iterator[Session]:
    with _DATA, database.session(MODULE) as session:
        yield session


class DatabaseStore:
    """`WalletStore` on the feature's database. Thread safe; `transaction` is a re-entrant lock per company
    (the in-process stand-in of the advisory lock of README 6.9)."""

    def __init__(self) -> None:
        self._txn_guard = threading.Lock()
        self._txn: dict[str, threading.RLock] = {}
        database.create_tables(MODULE)

    # ------------------------------------------------------------------------------------ wallets
    def get_wallet(self, company_id: str) -> dict | None:
        with _session() as session:
            return _plain(session.get(WalletRow, company_id))

    def put_wallet(self, wallet: dict) -> None:
        row = WalletRow.model_validate(wallet)
        if isinstance(row.bpn, str):
            row.bpn = row.bpn.upper()
        with _session() as session:
            session.merge(row)

    def _first(self, where: ColumnElement[bool]) -> dict | None:
        with _session() as session:
            return _plain(session.exec(select(WalletRow).where(where).limit(1)).first())

    def find_wallet_by_bpn(self, bpn: str) -> dict | None:
        return self._first(col(WalletRow.bpn) == (bpn.upper() if isinstance(bpn, str) else bpn))

    def find_wallet_by_did(self, did: str) -> dict | None:
        return self._first(col(WalletRow.did) == did) if did else None

    def list_wallets(self, statuses: list[str] | None = None) -> list[dict]:
        query = select(WalletRow)
        if statuses is not None:
            query = query.where(col(WalletRow.status).in_(statuses))
        with _session() as session:
            return [_row(row) for row in session.exec(query)]

    # ------------------------------------------------------------------------------------ secrets
    def put_secret(self, wallet_id: str, kind: str, url: str, client_id: str, secret_encrypted: bytes,
                   nonce: bytes, key_version: int) -> None:
        row = WalletSecretRow(wallet_id=wallet_id, kind=kind, url=url, client_id=client_id,
                              secret_encrypted=bytes(secret_encrypted), nonce=bytes(nonce), key_version=key_version,
                              created_at=dt.datetime.now(dt.UTC))
        with _session() as session:
            session.merge(row)

    def get_secret(self, wallet_id: str, kind: str) -> dict | None:
        with _session() as session:
            return _plain(session.get(WalletSecretRow, (wallet_id, kind)))

    def delete_secrets(self, wallet_id: str) -> None:
        with _session() as session:
            session.exec(delete(WalletSecretRow).where(col(WalletSecretRow.wallet_id) == wallet_id))

    # ------------------------------------------------------------------------- wallet accounts
    def get_account(self, technical_user_id: str) -> dict | None:
        """The row with a status other than DELETED, otherwise the latest one (README 7.2 step 2)."""
        query = select(WalletAccountRow).where(col(WalletAccountRow.technical_user_id) == technical_user_id)
        with _session() as session:
            rows = list(session.exec(query))
        if not rows:
            return None
        live = [row for row in rows if row.status != "DELETED"]
        return _row(max(live or rows, key=lambda row: row.created_at or _EARLIEST))

    def get_account_by_ref(self, wallet_account_ref: str) -> dict | None:
        with _session() as session:
            return _plain(session.get(WalletAccountRow, wallet_account_ref))

    def put_account(self, account: dict) -> None:
        with _session() as session:
            session.merge(WalletAccountRow.model_validate(account))

    def list_accounts(self, wallet_id: str | None = None, statuses: list[str] | None = None) -> list[dict]:
        query = select(WalletAccountRow)
        if wallet_id is not None:
            query = query.where(col(WalletAccountRow.wallet_id) == wallet_id)
        if statuses is not None:
            query = query.where(col(WalletAccountRow.status).in_(statuses))
        with _session() as session:
            return [_row(row) for row in session.exec(query)]

    def put_account_credentials(self, wallet_account_id: str, token_url: str, client_id: str,
                                client_secret_encrypted: bytes, nonce: bytes, key_version: int,
                                created_at: dt.datetime | str, expires_at: dt.datetime | str) -> None:
        row = WalletAccountCredentialsRow.model_validate({
            "wallet_account_id": wallet_account_id, "token_url": token_url, "client_id": client_id,
            "client_secret_encrypted": bytes(client_secret_encrypted), "nonce": bytes(nonce),
            "key_version": key_version, "created_at": created_at, "expires_at": expires_at})
        with _session() as session:
            session.merge(row)

    def get_account_credentials(self, wallet_account_id: str) -> dict | None:
        with _session() as session:
            return _plain(session.get(WalletAccountCredentialsRow, wallet_account_id))

    def delete_account_credentials(self, wallet_account_id: str) -> None:
        self.pop_account_credentials(wallet_account_id)

    def pop_account_credentials(self, wallet_account_id: str) -> dict | None:
        """Read and delete in one unit of work: of two concurrent callers exactly one gets the row (README 7.3)."""
        with _session() as session:
            row = session.get(WalletAccountCredentialsRow, wallet_account_id)
            if row is not None:
                session.delete(row)
            return _plain(row)

    # ------------------------------------------------------------------- audit log and step log
    def _append(self, table: type[AuditLogRow] | type[StepLogRow], entry: dict) -> None:
        with _session() as session:
            session.add(table.model_validate(entry))

    def _list(self, table: type[AuditLogRow] | type[StepLogRow]) -> list[dict]:
        with _session() as session:
            return [_row(row) for row in session.exec(select(table).order_by(col(table.seq)))]

    def append_audit(self, entry: dict) -> None:
        self._append(AuditLogRow, entry)

    def list_audit(self) -> list[dict]:
        return self._list(AuditLogRow)

    def append_step_log(self, entry: dict) -> None:
        self._append(StepLogRow, entry)

    def list_step_log(self) -> list[dict]:
        return self._list(StepLogRow)

    # ------------------------------------------------------------------------------ transactions
    @contextlib.contextmanager
    def transaction(self, company_id: str) -> Iterator[None]:
        with self._txn_guard:
            lock = self._txn.setdefault(company_id, threading.RLock())
        with lock:
            yield

    # ------------------------------------------------------------------------------- dump, reset
    def dump(self) -> dict:
        with _session() as session:
            return {name: _jsonable([_row(row) for row in session.exec(select(table))])
                    for name, table in _DUMP.items()}

    def reset(self) -> None:
        with _DATA:
            database.reset_tables(MODULE)

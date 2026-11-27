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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Repository of the registration (spec C1-M2 README 5): applications, document contents, used attestations and
the audit log in the feature's own database (`portal_common.database`). The only code that opens a session.

`applications_lock` stands for the row locks and partial unique indexes of 6.11: a service holds it while it
reads the state it decides on and writes the result, so two requests never act on the same old state.
"""
from __future__ import annotations

import threading
import weakref
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext

from sqlalchemy import func
from sqlmodel import Session, col, select

from features.registration.models import MODULE
from features.registration.models.tables import (
    ApplicationRow,
    AuditRow,
    DocumentContentRow,
    UsedAttestationRow,
)
from features.registration.models.value_sets import OPEN_STATUSES
from portal_common import database

applications_lock = threading.RLock()
_ready: weakref.WeakSet = weakref.WeakSet()
_in_memory_turns = threading.RLock()


def create_tables() -> None:
    database.create_tables(MODULE)
    _ready.add(database.engine(MODULE))


def reset() -> None:
    """Empty state of every table of the feature (the reference catalogue seeds its terms afterwards)."""
    with applications_lock, _turn():
        database.reset_tables(MODULE)
        _ready.add(database.engine(MODULE))


def _turn() -> AbstractContextManager:
    """The private in-memory database has one connection for all threads, so its units of work take turns;
    a database server keeps them apart itself."""
    return _in_memory_turns if database.url(MODULE) == database.IN_MEMORY else nullcontext()


@contextmanager
def session() -> Iterator[Session]:
    """A unit of work; creates the tables first when a caller (another feature in-process) comes before
    `on_startup()` of this feature."""
    if database.engine(MODULE) not in _ready:
        create_tables()
    with _turn(), database.session(MODULE) as current:
        yield current


# ------------------------------------------------------------------------------- applications
def get(application_id: str | None) -> ApplicationRow | None:
    if not application_id:
        return None
    with session() as s:
        return s.get(ApplicationRow, application_id)


def get_many(application_ids: Iterable[str]) -> dict[str, ApplicationRow]:
    """The applications with these IDs by ID, in one query."""
    ids = list(set(application_ids))
    if not ids:
        return {}
    with session() as s:
        return {row.id: row for row in s.exec(select(ApplicationRow).where(col(ApplicationRow.id).in_(ids)))}


def open_of_applicant(sub: str) -> ApplicationRow | None:
    """The open application of a person (6.11: at most one)."""
    with session() as s:
        return s.exec(select(ApplicationRow).where(ApplicationRow.applicant_sub == sub,
                                                   col(ApplicationRow.status).in_(OPEN_STATUSES))).first()


def company_has_open(company_id: str) -> bool:
    """6.11: at most one open application per existing company."""
    with session() as s:
        query = select(ApplicationRow.id).where(ApplicationRow.company_id == company_id,
                                                col(ApplicationRow.status).in_(OPEN_STATUSES))
        return s.exec(query).first() is not None


def company_id_used(company_id: str) -> bool:
    with session() as s:
        return s.exec(select(ApplicationRow.id).where(ApplicationRow.company_id == company_id)).first() is not None


def search(*, applicant_sub: str | None = None, statuses: Iterable[str] | None = None,
           kinds: Iterable[str] | None = None, verifications: Iterable[str] | None = None,
           company_id: str | None = None) -> list[ApplicationRow]:
    """Applications matching every given filter, newest first."""
    query = select(ApplicationRow)
    if applicant_sub is not None:
        query = query.where(ApplicationRow.applicant_sub == applicant_sub)
    if company_id:
        query = query.where(ApplicationRow.company_id == company_id)
    for column, values in ((ApplicationRow.status, statuses), (ApplicationRow.kind, kinds),
                           (ApplicationRow.verification, verifications)):
        if values:
            query = query.where(col(column).in_(list(values)))
    with session() as s:
        return list(s.exec(query.order_by(col(ApplicationRow.seq).desc())))


def next_seq() -> int:
    """Creation order of the next application; called under `applications_lock`."""
    with session() as s:
        return (s.exec(select(func.max(ApplicationRow.seq))).one() or 0) + 1


def save(row: ApplicationRow, *, audit: AuditRow | None = None, used_jti: str | None = None) -> None:
    """Insert or update the application, with its audit entry and the attestation it used, in one transaction."""
    with session() as s:
        s.merge(row)
        if used_jti:
            s.add(UsedAttestationRow(jti=used_jti))
        if audit is not None:
            s.add(audit)


def attestation_used(jti: str) -> bool:
    with session() as s:
        return s.get(UsedAttestationRow, jti) is not None


# ------------------------------------------------------------------------------ documents
def add_document(row: ApplicationRow, document_id: str, content: bytes, audit: AuditRow) -> None:
    with session() as s:
        s.merge(row)
        s.add(DocumentContentRow(document_id=document_id, application_id=row.id, content=content))
        s.add(audit)


def document_content(document_id: str) -> bytes | None:
    with session() as s:
        found = s.get(DocumentContentRow, document_id)
        return found.content if found else None


def delete_document(row: ApplicationRow, document_id: str, audit: AuditRow) -> None:
    with session() as s:
        s.merge(row)
        if found := s.get(DocumentContentRow, document_id):
            s.delete(found)
        s.add(audit)


# ------------------------------------------------------------------------------ audit log
def audit(entry: AuditRow) -> None:
    with session() as s:
        s.add(entry)


def audit_log() -> list[AuditRow]:
    """The audit log in the order it was written."""
    with session() as s:
        return list(s.exec(select(AuditRow).order_by(col(AuditRow.id))))

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
"""Review cases and the audit log in the feature's own database (README 5, `portal_common.database`).

The only code that opens a session of C1-M3. `lock` stands for the row lock of 6.8 (`SELECT ... FOR UPDATE`):
a service holds it from reading a case to saving it, so two reviewers deciding at the same time produce exactly
one decision.
"""
from __future__ import annotations

import threading
from collections.abc import Iterable
from contextlib import AbstractContextManager

from sqlalchemy import func
from sqlmodel import Session, col, select

from portal_common import database

from ..models.tables import AuditLogRow, ReviewCaseRow
from ..models.value_sets import MODULE

lock = threading.RLock()
_created: set[str] = set()   # database URLs whose tables exist


def create_tables() -> None:
    database.create_tables(MODULE)
    _created.add(database.url(MODULE))


def reset() -> None:
    with lock:
        database.reset_tables(MODULE)
        _created.add(database.url(MODULE))


def _session() -> AbstractContextManager[Session]:
    """A session of C1-M3; creates the tables first if neither `on_startup()` nor `reset()` ran (in-process use)."""
    if database.url(MODULE) not in _created:
        create_tables()
    return database.session(MODULE)


def get(case_id: str) -> ReviewCaseRow | None:
    with _session() as session:
        return session.get(ReviewCaseRow, case_id)


def by_application(application_id: str) -> ReviewCaseRow | None:
    with _session() as session:
        return session.exec(select(ReviewCaseRow).where(ReviewCaseRow.application_id == application_id)).first()


def next_seq() -> int:
    with _session() as session:
        return (session.exec(select(func.max(col(ReviewCaseRow.seq)))).one() or 0) + 1


def save(case: ReviewCaseRow) -> ReviewCaseRow:
    """Insert or update a case; the JSON columns are written as a whole."""
    with _session() as session:
        return session.merge(case)


def find(statuses: Iterable[str], kinds: Iterable[str] | None, verifications: Iterable[str] | None,
         application_id: str | None, page: int, size: int) -> tuple[list[ReviewCaseRow], int]:
    """One page of the cases that match the filters of 7.1, oldest first, and the number of all matches."""
    query = select(ReviewCaseRow).where(col(ReviewCaseRow.status).in_(list(statuses)))
    if kinds:
        query = query.where(col(ReviewCaseRow.kind).in_(list(kinds)))
    if verifications:
        query = query.where(col(ReviewCaseRow.verification).in_(list(verifications)))
    if application_id:
        query = query.where(ReviewCaseRow.application_id == application_id)
    with _session() as session:
        total = session.exec(select(func.count()).select_from(query.subquery())).one()
        rows = list(session.exec(query.order_by(col(ReviewCaseRow.seq)).offset(page * size).limit(size)))
    return rows, total


def count() -> int:
    with _session() as session:
        return session.exec(select(func.count()).select_from(ReviewCaseRow)).one()


def audit(entry: AuditLogRow) -> None:
    with _session() as session:
        session.add(entry)


def audit_log() -> list[AuditLogRow]:
    with _session() as session:
        return list(session.exec(select(AuditLogRow).order_by(col(AuditLogRow.id))))

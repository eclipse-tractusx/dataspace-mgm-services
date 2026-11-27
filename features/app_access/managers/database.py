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
#  Assisted-By: GitHub Copilot (claude-opus-5-5)
#################################################################################
"""The database `c2_m2` of App Access through `portal_common.database` (SQLAlchemy with SQLModel, F17).

The URL is `APP_ACCESS_DATABASE_URL`, `C2_M2_DATABASE_URL` or `DATABASE_URL`; without one the feature runs on its
private in-memory SQLite database. PostgreSQL gets its schema from the Alembic migrations in `managers/migrations/`
(version table `alembic_version_c2_m2`), SQLite from the tables of `models/tables.py`.
"""
from __future__ import annotations

import contextlib
import contextvars
import threading
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import func, select
from sqlmodel import Session

from features.app_access.managers.ports import Database
from features.app_access.models import tables  # noqa: F401 - registers the tables in the feature's MetaData
from features.app_access.models.exception import C2M2BaseException
from features.app_access.models.utils import MODULE
from portal_common import database
from portal_common.problems import Problem

VERSION_TABLE = "alembic_version_c2_m2"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

_current: contextvars.ContextVar[Session | None] = contextvars.ContextVar("app_access_session", default=None)
# The in-memory SQLite database is one connection for every thread: its transactions run one after the other.
_sqlite = threading.RLock()


def _is_sqlite() -> bool:
    return database.url(MODULE).startswith("sqlite")


def create_schema() -> None:
    """The tables of the feature: Alembic `upgrade head` on PostgreSQL, `create_all` on SQLite."""
    if _is_sqlite():
        database.create_tables(MODULE)
        return
    from alembic import command
    from alembic.config import Config as AlembicConfig
    config = AlembicConfig()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    with database.engine(MODULE).connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def reset_schema() -> None:
    """Empty tables (`reset()` of the index and tests)."""
    with _sqlite if _is_sqlite() else contextlib.nullcontext():
        database.reset_tables(MODULE)


class FeatureDatabase(Database):
    """Sessions of `portal_common.database` bound to the running transaction, and the locks of 6.14."""

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        """One session for everything inside; nested calls join it. Domain errors (Problem Details) commit what
        was saved before them, as the README expects (for example failed name checks); other errors roll back."""
        if _current.get() is not None:
            yield
            return
        with _sqlite if _is_sqlite() else contextlib.nullcontext(), database.session(MODULE) as session:
            token = _current.set(session)
            try:
                yield
            except (C2M2BaseException, Problem):
                session.commit()
                raise
            finally:
                _current.reset(token)

    @staticmethod
    def session() -> Session:
        """The session of the running transaction."""
        session = _current.get()
        if session is None:
            raise RuntimeError("no open transaction: call inside FeatureDatabase.transaction()")
        return session

    @contextlib.contextmanager
    def lock(self, name: str) -> Iterator[None]:
        """A transaction-scoped advisory lock on PostgreSQL; SQLite runs its transactions one by one anyway."""
        with self.transaction():
            session = self.session()
            if session.get_bind().dialect.name == "postgresql":
                session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(name, 0))))
            yield


__all__ = ["MIGRATIONS_DIR", "VERSION_TABLE", "FeatureDatabase", "create_schema", "reset_schema"]

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
"""Alembic environment of the database c2_m2: the connection of `database.create_schema()`, or the feature's
database URL (CLI: APP_ACCESS_DATABASE_URL, C2_M2_DATABASE_URL or DATABASE_URL). The target is the feature's own
MetaData (`models/tables.py`), so `alembic revision --autogenerate` compares against the SQLModel tables."""
from __future__ import annotations

from alembic import context
from sqlalchemy import Connection, func, pool, select

from features.app_access.managers.database import VERSION_TABLE
from features.app_access.models import tables  # noqa: F401 - registers the tables in the feature's MetaData
from features.app_access.models.utils import MODULE
from portal_common import database

TARGET = database.metadata(MODULE)


def run_offline() -> None:
    context.configure(url=database.url(MODULE), target_metadata=TARGET, literal_binds=True, version_table=VERSION_TABLE)
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    # one transaction for all pending migrations; the lock keeps replicas that start at once apart
    if connection.dialect.name == "postgresql":
        connection.execute(select(func.pg_advisory_xact_lock(func.hashtextextended("c2_m2:migrations", 0))))
    context.configure(connection=connection, target_metadata=TARGET, version_table=VERSION_TABLE)
    with context.begin_transaction():
        context.run_migrations()
    connection.commit()


def run_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    from sqlalchemy import create_engine
    with create_engine(database.url(MODULE), poolclass=pool.NullPool).connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_offline()
else:
    run_online()

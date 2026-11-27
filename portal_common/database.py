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
"""The own database of every feature, with SQLAlchemy through SQLModel (ADR-0003, decision 6).

A feature defines its tables as SQLModel classes on its own base, so its tables live in its own `MetaData`
and are created only in its own database:

    # features/<feature>/models/tables.py
    Table = database.table_base(MODULE)

    class CompanyRow(Table, table=True):
        __tablename__ = "company"
        company_id: str = Field(primary_key=True)
        legal_name: str

    # features/<feature>/managers/company_repository.py
    with database.session(MODULE) as session:
        session.add(CompanyRow(company_id=..., legal_name=...))

Table rows and API models combine: a row is a pydantic model, so `Company.model_validate(row,
from_attributes=True)` turns it into the response model, and fields shared by both can sit in one SQLModel
base without `table=True`.

The database of a feature is chosen at call time (root AGENTS.md rule 6), in this order:
1. `<FEATURE>_DATABASE_URL` (`COMPANY_PROFILE_DATABASE_URL`), the variable of ADR-0003;
2. `<SPEC_ID>_DATABASE_URL` (`C3_M1_DATABASE_URL`), the interim variable of #54;
3. `DATABASE_URL`, the variable of the spec, meant for a runtime that serves this one feature;
4. none: a private in-memory SQLite database, so tests and `demo.py` run without a server.

`postgresql://` URLs use the pg8000 driver of the image.
"""
from __future__ import annotations

import os
import types
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, MetaData
from sqlalchemy.orm import registry
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from . import layout

IN_MEMORY = "sqlite://"

_bases: dict[str, type[SQLModel]] = {}
_engines: dict[tuple[str, str], Engine] = {}


def _key(module: str) -> str:
    return module.lower()


def table_base(module: str) -> type[SQLModel]:
    """The base class of the feature's tables. Each module gets its own registry and `MetaData`, so
    `create_tables()` only touches the tables of that module, in that module's database."""
    key = _key(module)
    if key not in _bases:
        name = "".join(part.capitalize() for part in (layout.feature(key) or key.replace("-", "_")).split("_"))
        _bases[key] = types.new_class(f"{name}Table", (SQLModel,), {"registry": registry()})
    return _bases[key]


def metadata(module: str) -> MetaData:
    return table_base(module).metadata


def variables(module: str) -> list[str]:
    """The environment variables that name the module's database, in the order they are read."""
    names = [f"{module.replace('-', '_').upper()}_DATABASE_URL", "DATABASE_URL"]
    feature = layout.feature(module)
    return ([f"{feature.upper()}_DATABASE_URL"] if feature else []) + names


def url(module: str) -> str:
    """The database URL of the module, read at call time; an in-memory SQLite database when none is set."""
    for name in variables(module):
        if value := os.environ.get(name, "").strip():
            return _with_driver(value)
    return IN_MEMORY


def _with_driver(value: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if value.startswith(prefix):
            return "postgresql+pg8000://" + value[len(prefix):]
    return value


def engine(module: str) -> Engine:
    """The engine of the module's database; one per module and URL, so pools are not shared between features."""
    key = (_key(module), url(module))
    if key not in _engines:
        if key[1] == IN_MEMORY:
            # one connection for all threads, otherwise every connection would see its own empty database
            _engines[key] = create_engine(IN_MEMORY, poolclass=StaticPool, connect_args={"check_same_thread": False})
        else:
            _engines[key] = create_engine(key[1], pool_pre_ping=True)
    return _engines[key]


@contextmanager
def session(module: str) -> Iterator[Session]:
    """A unit of work in the module's database: committed when the block ends, rolled back on an error."""
    with Session(engine(module), expire_on_commit=False) as current:
        try:
            yield current
            current.commit()
        except BaseException:
            current.rollback()
            raise


def create_tables(module: str) -> None:
    """Create the module's tables that do not exist yet (start-up)."""
    metadata(module).create_all(engine(module))


def reset_tables(module: str) -> None:
    """Empty state: drop and recreate the module's tables (`reset()` of the index, tests)."""
    meta = metadata(module)
    meta.drop_all(engine(module))
    meta.create_all(engine(module))


def dispose() -> None:
    """Close every pool, e.g. after a test changed a database variable."""
    while _engines:
        _engines.popitem()[1].dispose()


def check_isolation(entries: Iterable[Any]) -> None:
    """Enforce that a runtime serving more than one feature does not silently share DATABASE_URL
    (ADR-0003 decision 6, FRAMEWORK 4.9).

    A runtime with more than one feature refuses to start when DATABASE_URL is set unless every
    served feature has a dedicated database variable configured (<FEATURE>_DATABASE_URL or
    <SPEC_ID>_DATABASE_URL).
    """
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        return

    entries_list = list(entries)
    if len(entries_list) <= 1:
        return

    missing: dict[str, list[str]] = {}
    for e in entries_list:
        mid = getattr(e, "id", str(e))
        own_vars = [v for v in variables(mid) if v != "DATABASE_URL"]
        if not any(os.environ.get(v, "").strip() for v in own_vars):
            missing[mid] = own_vars

    if missing:
        formatted = ", ".join(f"{mid} ({' or '.join(vars)})" for mid, vars in missing.items())
        raise ValueError(
            f"Multi-feature runtime cannot start with shared DATABASE_URL: each feature requires its own "
            f"database variable (ADR-0003 decision 6, FRAMEWORK 4.9). Missing variables for: {formatted}"
        )


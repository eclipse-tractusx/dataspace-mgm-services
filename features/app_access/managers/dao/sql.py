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
"""The DAOs of C2-M2 on the SQLModel tables of `models/tables.py` (README 5), for PostgreSQL and the in-memory
SQLite database alike. Every call runs in the transaction of `FeatureDatabase` (joined when one is open), and
records leave as copies (the internal dataclasses of `models/internal/`), never as attached rows."""
from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import enum
import functools
import types
import typing
from collections.abc import Callable, Iterable, Iterator
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

from sqlalchemy import ColumnElement
from sqlmodel import Session, SQLModel, col, select

from features.app_access.managers.dao.app_client_template_dao import AppClientTemplateDao
from features.app_access.managers.dao.app_instance_client_dao import AppInstanceClientDao
from features.app_access.managers.dao.audit_log_dao import AuditLogDao
from features.app_access.managers.dao.company_dao import CompanyDao
from features.app_access.managers.dao.company_user_dao import CompanyUserDao
from features.app_access.managers.dao.dao_service import DaoService
from features.app_access.managers.dao.invitation_dao import InvitationDao
from features.app_access.managers.dao.role_assignment_log_dao import RoleAssignmentLogDao
from features.app_access.managers.database import FeatureDatabase
from features.app_access.models.common import Actor
from features.app_access.models.constants import BindingStatus, InstanceClientStatus, InstanceKind, InvitationKind
from features.app_access.models.internal import (
    AppClientTemplate,
    AppInstanceClient,
    AuditLogEntry,
    Company,
    CompanyUser,
    Invitation,
    RoleAssignmentLogEntry,
    SuspendedRoles,
)
from features.app_access.models.tables import (
    AppClientTemplateRow,
    AppInstanceClientRow,
    AuditLogRow,
    ClientNumberRow,
    CompanyRow,
    CompanyUserRow,
    InvitationRow,
    RoleAssignmentLogRow,
)

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

type Where = bool | ColumnElement[bool]   # a condition on a column (SQLModel types a column as its value)

CURRENT = (BindingStatus.ACTIVE, BindingStatus.DISABLED)   # at most one binding of an account has one of them


# -- record <-> row ----------------------------------------------------------------------------------
def _encode(value: object) -> object:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, SuspendedRoles):
        return {"portal_roles": list(value.portal_roles), "app_roles": [list(r) for r in value.app_roles]}
    if isinstance(value, Actor):
        return {k: _encode(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, list):
        return list(value)
    return value


def _decode(hint: object, value: object) -> object:
    """A column value as the field of the record with the type `hint`."""
    if value is None:
        return None
    if typing.get_origin(hint) in (typing.Union, types.UnionType):
        hint = next(h for h in typing.get_args(hint) if h is not type(None))
    if isinstance(hint, type) and issubclass(hint, enum.Enum):
        return hint(value)
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.UTC)   # SQLite keeps no time zone
    if hint is SuspendedRoles and isinstance(value, dict):
        return SuspendedRoles(list(value["portal_roles"]), [tuple(r) for r in value["app_roles"]])
    if hint is Actor and isinstance(value, dict):
        return _build(Actor, {k: _decode(h, value.get(k)) for k, h in _hints(Actor).items()})
    if isinstance(value, list):
        return list(value)
    return value


@functools.cache
def _hints(record_type: type) -> dict[str, object]:
    return typing.get_type_hints(record_type)


def _build[R](record_type: type[R], values: dict[str, object]) -> R:
    """The record from its decoded fields (the field types are checked by `_decode`)."""
    factory: Callable[..., R] = record_type
    return factory(**values)


def to_row(row_type: type[SQLModel], record: DataclassInstance) -> SQLModel:
    return row_type(**{f.name: _encode(getattr(record, f.name)) for f in dataclasses.fields(record)})


def to_record[R: DataclassInstance](record_type: type[R], row: SQLModel | None) -> R | None:
    if row is None:
        return None
    hints = _hints(record_type)
    fields = dataclasses.fields(record_type)
    return _build(record_type, {f.name: _decode(hints[f.name], getattr(row, f.name)) for f in fields})


class _SqlDao[R: DataclassInstance]:
    ROW: type[SQLModel]
    RECORD: type[R]

    def __init__(self, db: FeatureDatabase) -> None:
        self.db = db

    @contextlib.contextmanager
    def _session(self) -> Iterator[Session]:
        with self.db.transaction():
            yield self.db.session()

    def _get(self, key: str) -> R | None:
        with self._session() as session:
            return to_record(self.RECORD, session.get(self.ROW, key))

    def _save(self, record: R) -> None:
        with self._session() as session:
            session.merge(to_row(self.ROW, record))

    def _all(self, *where: Where, order: str) -> list[R]:
        """The records that match, ordered by the column `order`."""
        statement = select(self.ROW).where(*where).order_by(col(getattr(self.ROW, order)))
        with self._session() as session:
            return [r for row in session.exec(statement) if (r := to_record(self.RECORD, row)) is not None]

    def _first(self, *where: Where) -> R | None:
        with self._session() as session:
            return to_record(self.RECORD, session.exec(select(self.ROW).where(*where)).first())


class SqlCompanyDao(_SqlDao[Company], CompanyDao):
    ROW, RECORD = CompanyRow, Company

    def lock(self, company_id: str) -> AbstractContextManager[None]:
        return self.db.lock(f"c2_m2:company:{company_id}")

    def get(self, company_id: str) -> Company | None:
        return self._get(company_id)

    def save(self, company: Company) -> None:
        self._save(company)


class SqlCompanyUserDao(_SqlDao[CompanyUser], CompanyUserDao):
    ROW, RECORD = CompanyUserRow, CompanyUser

    def lock_account(self, user_id: str) -> AbstractContextManager[None]:
        return self.db.lock(f"c2_m2:account:{user_id}")

    def save(self, binding: CompanyUser) -> None:
        self._save(binding)

    def current_of(self, user_id: str) -> CompanyUser | None:
        return self._first(CompanyUserRow.user_id == user_id, col(CompanyUserRow.status).in_(CURRENT))

    def list_of(self, user_id: str, company_id: str) -> list[CompanyUser]:
        return self._all(CompanyUserRow.user_id == user_id, CompanyUserRow.company_id == company_id,
                         order="created_at")

    def list_of_company(self, company_id: str | None, statuses: Iterable[BindingStatus]) -> list[CompanyUser]:
        where: list[Where] = [col(CompanyUserRow.status).in_([s.value for s in statuses])]
        if company_id is not None:
            where.append(CompanyUserRow.company_id == company_id)
        return self._all(*where, order="created_at")


class SqlAppClientTemplateDao(_SqlDao[AppClientTemplate], AppClientTemplateDao):
    ROW, RECORD = AppClientTemplateRow, AppClientTemplate

    def lock(self, app_id: str) -> AbstractContextManager[None]:
        return self.db.lock(f"c2_m2:app:{app_id}")

    def get(self, app_id: str) -> AppClientTemplate | None:
        return self._get(app_id)

    def save(self, template: AppClientTemplate) -> None:
        self._save(template)


class SqlAppInstanceClientDao(_SqlDao[AppInstanceClient], AppInstanceClientDao):
    ROW, RECORD = AppInstanceClientRow, AppInstanceClient

    def get(self, instance_client_id: str) -> AppInstanceClient | None:
        return self._get(instance_client_id)

    def save(self, instance_client: AppInstanceClient) -> None:
        self._save(instance_client)

    def find_by_subscription(self, offer_subscription_id: str) -> AppInstanceClient | None:
        return self._first(AppInstanceClientRow.offer_subscription_id == offer_subscription_id)

    def find_single(self, app_id: str) -> AppInstanceClient | None:
        return self._first(AppInstanceClientRow.app_id == app_id,
                           AppInstanceClientRow.instance_kind == InstanceKind.SINGLE.value,
                           AppInstanceClientRow.status != InstanceClientStatus.DISABLED.value)

    def find_by_iam_client_id(self, iam_client_id: str) -> AppInstanceClient | None:
        return self._first(AppInstanceClientRow.iam_client_id == iam_client_id)

    def list_of_app(self, app_id: str) -> list[AppInstanceClient]:
        return self._all(AppInstanceClientRow.app_id == app_id, order="created_at")

    def list_all(self) -> list[AppInstanceClient]:
        return self._all(order="created_at")

    def next_client_number(self) -> int:
        """The sequence `client_number` (6.1), 1, 2, ...; the row is locked until the transaction ends."""
        with self._session() as session:
            row = session.get(ClientNumberRow, "client_number", with_for_update=True)
            if row is None:
                row = ClientNumberRow(name="client_number", value=0)
            row.value += 1
            session.add(row)
            return row.value


class SqlInvitationDao(_SqlDao[Invitation], InvitationDao):
    ROW, RECORD = InvitationRow, Invitation

    def lock(self, invitation_id: str) -> AbstractContextManager[None]:
        return self.db.lock(f"c2_m2:invitation:{invitation_id}")

    def lock_staff(self) -> AbstractContextManager[None]:
        return self.db.lock("c2_m2:staff:all")

    def get(self, invitation_id: str) -> Invitation | None:
        return self._get(invitation_id)

    def save(self, invitation: Invitation) -> None:
        self._save(invitation)

    def find_by_code_hash(self, code_hash: str) -> Invitation | None:
        return self._first(InvitationRow.code_hash == code_hash)

    def list_of(self, kind: InvitationKind, company_id: str | None) -> list[Invitation]:
        where: list[Where] = [InvitationRow.kind == kind.value]
        if company_id is not None:
            where.append(InvitationRow.company_id == company_id)
        return self._all(*where, order="created_at")

    def list_all(self) -> list[Invitation]:
        return self._all(order="created_at")


class SqlAuditLogDao(_SqlDao[AuditLogEntry], AuditLogDao):
    ROW, RECORD = AuditLogRow, AuditLogEntry

    def add(self, entry: AuditLogEntry) -> None:
        self._save(entry)

    def list_all(self) -> list[AuditLogEntry]:
        return self._all(order="occurred_at")


class SqlRoleAssignmentLogDao(_SqlDao[RoleAssignmentLogEntry], RoleAssignmentLogDao):
    ROW, RECORD = RoleAssignmentLogRow, RoleAssignmentLogEntry

    def add(self, entry: RoleAssignmentLogEntry) -> None:
        self._save(entry)

    def list_all(self) -> list[RoleAssignmentLogEntry]:
        return self._all(order="occurred_at")


def sql_dao_service(db: FeatureDatabase | None = None) -> DaoService:
    """Every DAO on the tables of the feature's database."""
    db = db or FeatureDatabase()
    return DaoService(db, SqlAppClientTemplateDao(db), SqlAppInstanceClientDao(db), SqlCompanyDao(db),
                      SqlCompanyUserDao(db), SqlInvitationDao(db), SqlAuditLogDao(db), SqlRoleAssignmentLogDao(db))


__all__ = ["SqlAppClientTemplateDao", "SqlAppInstanceClientDao", "SqlAuditLogDao", "SqlCompanyDao",
           "SqlCompanyUserDao", "SqlInvitationDao", "SqlRoleAssignmentLogDao", "sql_dao_service", "to_record",
           "to_row"]

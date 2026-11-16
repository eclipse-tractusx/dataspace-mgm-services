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
"""The tables of the database `c2_m2` (README 5) as SQLModel classes on the feature's own base, so they live in the
feature's own `MetaData` and database (`portal_common.database`, F17).

A row has the fields of the internal record of the same name in `models/internal/` (`CompanyUserRow` ->
`CompanyUser`); `managers/dao/sql.py` converts between the two. Value sets are stored as their `str` value, nested
values (roles, suspended roles, the actor of a log entry) as JSON. The columns the DAOs look up by are indexed.
"""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime
from sqlmodel import Field, SQLModel

from features.app_access.models.utils import MODULE
from portal_common import database

if TYPE_CHECKING:  # a class built at run time is no valid base class for mypy
    Table = SQLModel
else:
    Table = database.table_base(MODULE)
Timestamp = DateTime(timezone=True)


class AppClientTemplateRow(Table, table=True):
    __tablename__ = "app_client_template"
    app_id: str = Field(primary_key=True)
    provider_company_id: str
    app_name: str
    iam_client_id: str = Field(unique=True)
    iam_client_uuid: str | None = None
    created_at: dt.datetime = Field(sa_type=Timestamp)
    changed_at: dt.datetime = Field(sa_type=Timestamp)


class AppInstanceClientRow(Table, table=True):
    __tablename__ = "app_instance_client"
    id: str = Field(primary_key=True)
    app_id: str = Field(index=True)
    instance_kind: str
    offer_subscription_id: str | None = Field(default=None, unique=True)
    customer_company_id: str | None = Field(default=None, index=True)
    iam_client_id: str = Field(unique=True)
    instance_url: str
    status: str
    iam_client_uuid: str | None = None
    created_at: dt.datetime = Field(sa_type=Timestamp, index=True)
    changed_at: dt.datetime = Field(sa_type=Timestamp)


class ClientNumberRow(Table, table=True):
    """The sequence `client_number` of 6.1: the last number handed out."""
    __tablename__ = "client_number"
    name: str = Field(primary_key=True)
    value: int


class CompanyRow(Table, table=True):
    __tablename__ = "company"
    company_id: str = Field(primary_key=True)
    bpn: str | None = None
    status: str
    created_at: dt.datetime = Field(sa_type=Timestamp)
    changed_at: dt.datetime = Field(sa_type=Timestamp)


class CompanyUserRow(Table, table=True):
    __tablename__ = "company_user"
    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    company_id: str = Field(index=True)
    joined_via: str
    given_name: str | None = None
    family_name: str | None = None
    status: str = Field(index=True)
    invitation_id: str | None = None
    removal_reason: str | None = None
    suspended_roles: dict | None = Field(default=None, sa_type=JSON)
    created_at: dt.datetime = Field(sa_type=Timestamp)
    changed_at: dt.datetime = Field(sa_type=Timestamp)
    removed_at: dt.datetime | None = Field(default=None, sa_type=Timestamp)


class InvitationRow(Table, table=True):
    __tablename__ = "invitation"
    id: str = Field(primary_key=True)
    kind: str = Field(index=True)
    company_id: str | None = Field(default=None, index=True)
    given_name: str | None = None
    family_name: str | None = None
    roles: list = Field(sa_type=JSON)
    code_hash: str = Field(unique=True)
    expires_at: dt.datetime = Field(sa_type=Timestamp)
    created_by: str | None = None
    status: str
    end_reason: str | None = None
    failed_attempts: int = 0
    accepted_by: str | None = None
    accepted_at: dt.datetime | None = Field(default=None, sa_type=Timestamp)
    created_at: dt.datetime = Field(sa_type=Timestamp, index=True)
    ended_at: dt.datetime | None = Field(default=None, sa_type=Timestamp)


class AuditLogRow(Table, table=True):
    __tablename__ = "audit_log"
    id: str = Field(primary_key=True)
    actor: dict = Field(sa_type=JSON)
    operation: str
    company_id: str | None = None
    object_id: str | None = None
    occurred_at: dt.datetime = Field(sa_type=Timestamp, index=True)


class RoleAssignmentLogRow(Table, table=True):
    __tablename__ = "role_assignment_log"
    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    company_id: str | None = None
    role_kind: str
    iam_client_id: str
    role_name: str
    action: str
    actor: dict = Field(sa_type=JSON)
    operation: str
    app_id: str | None = None
    app_instance_client_id: str | None = None
    occurred_at: dt.datetime = Field(sa_type=Timestamp, index=True)

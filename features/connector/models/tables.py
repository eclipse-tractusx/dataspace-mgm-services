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
"""The tables of C6-M1 (README 5, FRAMEWORK 4.3) in the feature's own database (`portal_common.database`).

Status and type hold the values of `ConnectorStatus` and `ConnectorType`. The columns that the uniqueness rules
of README 5 and the steps look up by are indexed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Field, SQLModel

from portal_common import database

from .connector import MODULE

if TYPE_CHECKING:   # a class built at run time is no valid base class for mypy
    Table = SQLModel
else:
    Table = database.table_base(MODULE)


class ConnectorRow(Table, table=True):
    """Table `connector` (README 5); the primary key is the column `id`."""
    __tablename__ = "connector"

    connector_id: str = Field(primary_key=True, sa_column_kwargs={"name": "id"})
    name: str = Field(index=True)
    endpoint: str
    location: str
    type: str
    status: str = Field(index=True)
    provider_company_id: str = Field(index=True)
    host_company_id: str = Field(index=True)
    technical_user_id: str | None = Field(default=None, index=True)
    offer_subscription_id: str | None = Field(default=None, index=True)
    created_at: str
    changed_at: str | None = None


class AuditEntryRow(Table, table=True):
    """Table `audit_entry` (FRAMEWORK 4.3): time, acting person, company, operation, object. No secrets, no names."""
    __tablename__ = "audit_entry"

    id: int | None = Field(default=None, primary_key=True)
    at: str
    sub: str | None = None
    company_id: str | None = None
    operation: str
    object_id: str


class EndedSubscriptionRow(Table, table=True):
    """A subscription that step 8.1 has run for: no new connector for it (OPEN-QUESTIONS.md 8)."""
    __tablename__ = "ended_subscription"

    offer_subscription_id: str = Field(primary_key=True)


class DeletedTechnicalUserRow(Table, table=True):
    """An account that step 8.2 has run for (deleted in C2-M3): never linked again (OPEN-QUESTIONS.md 13)."""
    __tablename__ = "deleted_technical_user"

    technical_user_id: str = Field(primary_key=True)

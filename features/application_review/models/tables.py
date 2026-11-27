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
"""The tables of the application review in its own database (README 5, `portal_common.database`).

The nested parts of a review case (checks with their findings, first approval, decision, closure) are JSON
columns: they are always read and written with the case and never queried on their own. Their shape is
the one of the API models in `review_case.py`, in JSON field names.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from portal_common import database

from .value_sets import MODULE, Kind, Status, Verification

if TYPE_CHECKING:
    Table = SQLModel   # the static type of the base; at run time it is the feature's own base and MetaData
else:
    Table = database.table_base(MODULE)


class ReviewCaseRow(Table, table=True):
    """`review_case` with its `review_check` rows (README 5); one case per application."""

    __tablename__ = "review_case"

    id: str = Field(primary_key=True)
    application_id: str = Field(index=True, unique=True)
    company_id: str
    kind: Kind
    existing_company: bool
    verification: Verification
    applicant_sub: str | None = None
    status: Status = Field(index=True)
    opened_at: str
    seq: int = Field(index=True)   # order of opening: lists are sorted oldest first (7.1)
    csp_bpn: str | None = None
    checks: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))   # checkKey -> ReviewCheck
    rejected: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))  # checks a neighbour refused
    first_approval: dict | None = Field(default=None, sa_column=Column(JSON))
    decision: dict | None = Field(default=None, sa_column=Column(JSON))
    closure: dict | None = Field(default=None, sa_column=Column(JSON))
    changed_at: str


class AuditLogRow(Table, table=True):
    """`audit_log` (README 5, 6.9): who did what on which review case."""

    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    at: str
    sub: str | None = None
    process_id: str | None = None
    step_run_id: str | None = None
    company_id: str
    operation: str
    review_case_id: str = Field(index=True)
    application_id: str

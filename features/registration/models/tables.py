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
"""The tables of the registration (README 5) in its own database (`portal_common.database`, rule F17).

A row converts to its view with `Model.model_validate(row, from_attributes=True)`. Nested parts of an
application (company data, comparison, document metadata, consents, attestation extract) are JSON columns:
they are read and written with the application as a whole and never queried on their own. The JSON keeps
the camelCase field names of the API, so a view validates it unchanged.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, LargeBinary, UniqueConstraint
from sqlmodel import Field, SQLModel

from features.registration.models import MODULE
from features.registration.models.value_sets import (
    AgreementParty,
    AgreementScope,
    AgreementStatus,
    ApplicationKind,
    ApplicationStatus,
    Verification,
)
from portal_common import database

if TYPE_CHECKING:   # the base is built at run time; for the type checker it is an SQLModel
    Table = SQLModel
else:
    Table = database.table_base(MODULE)


def _json(default: Callable[[], object] = list) -> Any:  # noqa: ANN401 - the type of sqlmodel.Field()
    """A JSON column; `default` builds the value of a new row."""
    return Field(default_factory=default, sa_column=Column(JSON, nullable=True))


class ApplicationRow(Table, table=True):
    """One application with everything the views need; looked up by id, applicant and company."""

    __tablename__ = "application"

    id: str = Field(primary_key=True)
    seq: int = Field(index=True, description="creation order; lists show the newest first")
    company_id: str = Field(index=True)
    applicant_sub: str = Field(index=True)
    status: ApplicationStatus = Field(index=True)
    kind: ApplicationKind
    verification: Verification
    existing_company: bool
    applicant: dict = _json(dict)
    company_data: dict = _json(dict)
    company_roles: list = _json()
    comparison: list = _json()
    documents: list = _json()
    representation_declared: bool | None = None
    consents: list = _json()
    decline_reason: str | None = None
    created_at: str
    changed_at: str
    submitted_at: str | None = None
    withdrawn_at: str | None = None
    closed_at: str | None = None
    completed_at: str | None = None
    # internal, never in a view as such
    given: dict = _json(dict)                       # company data as the person declared it (6.5 is derived)
    required_agreements: list = _json()             # terms required at submission (9.1)
    consent_records: list = _json()                 # proof of the consents (README 5)
    attestation: dict | None = _json(lambda: None)  # `AttestationRecord`
    attestation_token: str | None = None            # the JWT, for the repeated signature check (9.1)
    attestation_claims: dict | None = _json(lambda: None)   # iat, exp and company of the attestation


class DocumentContentRow(Table, table=True):
    """The bytes of a supporting document; its metadata is in `ApplicationRow.documents`."""

    __tablename__ = "application_document"

    document_id: str = Field(primary_key=True)
    application_id: str = Field(index=True)
    content: bytes = Field(sa_column=Column(LargeBinary, nullable=False))


class UsedAttestationRow(Table, table=True):
    """`jti` of every attestation an application used: an attestation serves one application (6.4)."""

    __tablename__ = "used_attestation"

    jti: str = Field(primary_key=True)


class AuditRow(Table, table=True):
    """Audit log (README 5, 10): who did what with which application or terms."""

    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    at: str
    sub: str | None = None
    process_id: str | None = None
    step_run_id: str | None = None
    company_id: str | None = None
    operation: str
    application_id: str | None = Field(default=None, index=True)
    object_id: str | None = None


class AgreementVersionRow(Table, table=True):
    """A version of terms (README 6.8); `seq` keeps the order the versions were taken over or created in."""

    __tablename__ = "agreement_version"
    __table_args__ = (UniqueConstraint("agreement_key", "version"),)

    seq: int | None = Field(default=None, primary_key=True)
    agreement_key: str = Field(index=True)
    version: str
    party: AgreementParty
    scope: AgreementScope
    company_roles: list = _json()
    title: dict = _json(dict)
    document_urls: dict = _json(dict)
    status: AgreementStatus = Field(index=True)
    reconsent_required: bool = False
    reconsent_due_at: str | None = None
    created_at: str
    created_by: str | None = None

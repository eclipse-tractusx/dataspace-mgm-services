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
"""API models of the credentials (openapi.yaml `components/schemas`), on the shared bases of `portal_common.models`.

Field names are snake_case in Python and camelCase in JSON. Read models validate straight from the rows of the
store (`Model.model_validate(row)`); timestamps stay `datetime` and are written as ISO 8601 in JSON, as before.
"""
from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, PlainSerializer, field_validator

from features.credentials.models.values import (
    BPN_PATTERN,
    CredentialStatus,
    CredentialType,
    ReportStatus,
    RevocationReason,
    Route,
    RunStatus,
)
from portal_common.models import ApiModel, Page, StepRequest, Uuid


def _unique(types: list[CredentialType] | None) -> list[CredentialType] | None:
    if types is not None and len(set(types)) != len(types):
        raise ValueError("credentialTypes must be unique")
    return types


Timestamp = Annotated[dt.datetime, PlainSerializer(lambda value: value.isoformat(), when_used="json")]
"""A timezone-aware timestamp, in JSON as `datetime.isoformat()`."""

CompanyId = Annotated[Uuid, AfterValidator(str.lower)]
"""A company id as canonical lower-case UUID, the form the rows are stored with."""

CredentialTypes = Annotated[list[CredentialType] | None, Field(min_length=1), AfterValidator(_unique)]
"""`credentialTypes` of a step: absent or null = the default of the step, else a non-empty list of unique types."""

Bpn = Annotated[str, Field(pattern=BPN_PATTERN)]


# ------------------------------------------------------------------------------------------------ steps
class IssueCredentials(StepRequest):
    """`StepIssueCredentials` (README 8.1)."""

    company_id: CompanyId
    credential_types: CredentialTypes = None


class RevokeCredentials(StepRequest):
    """`StepRevokeCredentials` (README 8.2)."""

    company_id: CompanyId
    reason: RevocationReason
    credential_types: CredentialTypes = None


class CredentialOutcome(ApiModel):
    credential_type: CredentialType
    status: CredentialStatus


class IssueResult(ApiModel):
    """`result` of `StepResultCredentials`."""

    company_id: str
    credentials: list[CredentialOutcome]


class RevocationResult(ApiModel):
    """`result` of `StepResultRevocation`."""

    company_id: str
    revoked: list[CredentialType]
    cancelled: list[CredentialType]
    manual_revocation: list[CredentialType]


# ----------------------------------------------------------------------------------- issuers and staff
class IssuerReport(ApiModel):
    """`IssuerResponse`: status report of an issuer (README 7.4)."""

    bpn: Bpn
    status: ReportStatus
    message: str | None = None


class ConfirmRevocation(ApiModel):
    """Body of `confirm-revocation` (README 7.3)."""

    note: str = Field(min_length=1, max_length=500)


# ------------------------------------------------------------------------------------------------ views
class CredentialStatusView(ApiModel):
    """`CredentialStatusView`: no messages of the issuer, no route; `NONE` = never ordered (README 7.1, 9.1)."""

    credential_type: CredentialType
    status: CredentialStatus | Literal["NONE"]
    requested_at: Timestamp | None = None
    issued_at: Timestamp | None = None
    revoked_at: Timestamp | None = None


class IssuanceRunView(ApiModel):
    """`run` of `CompanyCredentialsInternal`: the last issuance round."""

    status: RunStatus
    credential_types: list[CredentialType]
    started_at: Timestamp | None = None
    finished_at: Timestamp | None = None


class CompanyCredentials(ApiModel):
    """`CompanyCredentialsInternal` (README 9.1)."""

    company_id: str
    credentials: list[CredentialStatusView]
    run: IssuanceRunView | None


class CredentialDetail(ApiModel):
    """`CredentialDetail`: the view of OSP staff, every field except secrets (README 7.2)."""

    id: str
    company_id: str
    credential_type: CredentialType
    status: CredentialStatus
    route: Route | None
    issuer_did: str | None = None
    wallet_provider: str | None = None
    bpn: str | None = None
    holder_did: str | None = None
    request_ref: str | None = None
    attempt: int
    requested_at: Timestamp | None = None
    issued_at: Timestamp | None = None
    failed_at: Timestamp | None = None
    revoked_at: Timestamp | None = None
    failure_reason: str | None = None
    revocation_reason: RevocationReason | None = None
    created_at: Timestamp
    changed_at: Timestamp

    @field_validator("issuer_did", "request_ref", mode="before")
    @classmethod
    def _empty_is_none(cls, value: str | None) -> str | None:
        """The routes without issuer DID or request reference store an empty string; the API shows null."""
        return value or None


CredentialPage = Page[CredentialDetail]


def as_json(model: ApiModel) -> dict:
    """The JSON form of a model for in-process callers, with the same keys as over HTTP (null fields included)."""
    return model.model_dump(mode="json", by_alias=True)

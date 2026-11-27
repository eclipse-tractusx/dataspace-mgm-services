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
"""Models of an application (spec C1-M2 openapi.yaml): the request bodies of 7.2 to 7.10 and the views
`Application`, `ApplicationWithReview`, `ApplicationInternal` and `ApplicationSummary`.

The request bodies are checked by `services.application_validation` first, in the order and with the messages of
README 6 and 7.2; these models then carry the checked values. They therefore accept further fields
(`additionalProperties` is not false in the spec). The views keep fields that a stored object never had out
of the JSON (`response_model_exclude_unset`), so an address without `region` stays without it.
"""
from __future__ import annotations

from typing import Literal

from pydantic import StrictBool

from features.registration.models.value_sets import (
    ApplicationKind,
    ApplicationStatus,
    Lang,
    ReviewStatus,
    SignatureResult,
    Verification,
)
from portal_common.models import ApiModel

ComparisonField = Literal["EBWOID", "EUID", "COUNTRY", "LEGAL_NAME", "STREET", "POSTAL_CODE", "CITY"]
ComparisonResult = Literal["FROM_ATTESTATION", "MATCH", "MISMATCH", "NOT_IN_ATTESTATION"]


# ------------------------------------------------------------------------------- company data
class Address(ApiModel):
    street_name: str | None = None
    street_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    region: str | None = None
    country_code: str | None = None


class Identifier(ApiModel):
    type: str
    value: str


class IdentifierWithSource(Identifier):
    source: Literal["ATTESTATION", "APPLICANT"]


class CompanyDataInput(ApiModel):
    """`CompanyDataInput`: what the person declares; EBW takes missing fields from the attestation (6.5)."""
    legal_name: str | None = None
    short_name: str | None = None
    address: Address | None = None
    identifiers: list[Identifier] | None = None


class CompanyData(ApiModel):
    legal_name: str
    short_name: str | None = None
    address: Address
    identifiers: list[IdentifierWithSource]


class ComparisonEntry(ApiModel):
    field: ComparisonField
    result: ComparisonResult


# -------------------------------------------------------------------------------- attestation
class PersonExtract(ApiModel):
    given_name: str
    family_name: str


class Representation(ApiModel):
    confirmed: bool
    result: str | None = None
    type: str | None = None
    role: str | None = None
    valid_until: str | None = None
    issuer: str | None = None
    trust: str | None = None
    reasons: list[str] = []


class AttestationSummary(ApiModel):
    """Extract of the current attestation in `Application`, without the JWT."""
    attestation_id: str
    issuer: str
    issued_at: str | None = None
    expires_at: str | None = None
    verified_at: str | None = None
    person: PersonExtract
    representation: Representation


class AttestedAddress(ApiModel):
    street_address: str | None = None
    postal_code: str | None = None
    locality: str | None = None
    country: str | None = None


class AttestedCompany(ApiModel):
    legal_name: str
    ebwoid: str
    euid: str | None = None
    country_code: str
    address: AttestedAddress | None = None


class Evidence(ApiModel):
    type: str
    vct: str
    issuer: str
    wallet: str
    status_checked: bool


class AttestationRecord(AttestationSummary):
    """What the module keeps of a verified attestation (README 5): `AttestationDetail` without the signature
    check, which is repeated at every query (9.1)."""
    key_id: str | None = None
    client_id: str
    company: AttestedCompany
    evidence: list[Evidence]


class SignatureCheck(ApiModel):
    result: SignatureResult
    checked_at: str


class AttestationDetail(AttestationRecord):
    signature_check: SignatureCheck


# ------------------------------------------------------------------------- documents, consents
class DocumentInfo(ApiModel):
    """Metadata of a supporting document, without content."""
    document_id: str
    document_type: str
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: str


class AgreementRef(ApiModel):
    agreement_key: str
    version: str


class ConsentInput(AgreementRef):
    language: Lang


class Consent(ConsentInput):
    given_at: str


class ConsentRecord(Consent):
    """Proof of a consent (README 5): who gave it with which attestation; internal, never in a view."""
    given_by_sub: str
    attestation_id: str | None = None


# ------------------------------------------------------------------------------ request bodies
class ApplicationCreate(ApiModel):
    """`ApplicationCreate` (7.2), after `check_create`."""
    kind: ApplicationKind
    verification: Verification
    attestation: str | None = None
    company_id: str | None = None
    bpn: str | None = None
    company_data: CompanyDataInput | None = None
    company_roles: list[str] | None = None


class ApplicationUpdate(ApiModel):
    """`ApplicationUpdate` (7.5): given fields replace, missing ones stay."""
    legal_name: str | None = None
    short_name: str | None = None
    address: Address | None = None
    identifiers: list[Identifier] | None = None
    company_roles: list[str] | None = None


class AttestationInput(ApiModel):
    attestation: str


class SubmitRequest(ApiModel):
    """`SubmitRequest` (7.10); `representationDeclared` only counts when it is `true`."""
    consents: list[ConsentInput]
    representation_declared: StrictBool | None = None


# ------------------------------------------------------------------------------------- views
class Applicant(ApiModel):
    sub: str
    given_name: str | None = None
    family_name: str | None = None


class Application(ApiModel):
    """`Application` (7.3)."""
    id: str
    company_id: str
    kind: ApplicationKind
    existing_company: bool
    verification: Verification
    applicant: Applicant
    status: ApplicationStatus
    company_data: CompanyData
    company_roles: list[str]
    attestation: AttestationSummary | None = None
    comparison: list[ComparisonEntry]
    documents: list[DocumentInfo]
    representation_declared: bool | None = None
    consents: list[Consent]
    decline_reason: str | None = None
    created_at: str
    changed_at: str
    submitted_at: str | None = None
    withdrawn_at: str | None = None
    closed_at: str | None = None
    completed_at: str | None = None


class ApplicationWithReview(Application):
    """`ApplicationWithReview` (7.4)."""
    review_status: ReviewStatus


class ApplicationInternal(Application):
    """`ApplicationInternal` (9.1): with the whole attestation and the terms recorded at submission."""
    attestation: AttestationDetail | None = None
    required_agreements: list[AgreementRef]


class ApplicationSummary(ApiModel):
    """`ApplicationSummary` (7.12, 9.2)."""
    id: str
    company_id: str
    kind: ApplicationKind
    existing_company: bool
    verification: Verification
    status: ApplicationStatus
    legal_name: str
    country_code: str | None = None
    company_roles: list[str]
    created_at: str
    submitted_at: str | None = None

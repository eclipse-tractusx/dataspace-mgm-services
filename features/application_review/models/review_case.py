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
"""Response models of the review cases (openapi.yaml `ReviewCase`, `ReviewCaseSummary`, `ReviewStatusInfo` and
the step results). Values that come from the neighbours (identifiers, BPNs, country codes) are typed as plain
strings, so a neighbour's answer is passed on as before instead of failing the response."""
from __future__ import annotations

from typing import Any

from portal_common.models import ApiModel, Page, Uuid

from .value_sets import CheckKey, CheckResult, ClosureReason, CspOutcome, FourEyesCase, Kind, Status, Verification


class CspMatch(ApiModel):
    """A CSP match, merged per BPN (README 6.3)."""

    bpn: str | None
    matched_by: list[str]
    home_osp_id: str | None = None
    home_osp_name: str | None = None
    home_is_this_osp: bool | None = None
    member_active: bool | None = None
    expected: bool


class Duplicate(ApiModel):
    company_id: str
    company_status: str | None = None
    matched_on: list[str]


class MissingAgreement(ApiModel):
    agreement_key: str
    version: str


class CheckDetails(ApiModel):
    """The finding of one check; each check sets only its own fields (README 6.2, 6.3)."""

    signature_check: str | None = None
    expired_at_submission: bool | None = None
    representation_reasons: list[str] | None = None
    mismatched_fields: list[str] | None = None
    unverified_fields: list[str] | None = None
    duplicates: list[Duplicate] | None = None
    csp_outcome: CspOutcome | None = None
    csp_matches: list[CspMatch] | None = None
    missing: list[MissingAgreement] | None = None
    error: str | None = None


class CheckOutcome(ApiModel):
    check_key: CheckKey
    result: CheckResult


class ReviewCheck(CheckOutcome):
    details: CheckDetails | None = None
    checked_at: str
    attempts: int


class CheckCounts(ApiModel):
    passed: int
    failed: int
    not_applicable: int
    error: int


class ApplicationBrief(ApiModel):
    """Summary of the application from C1-M2 (`ApplicationSummary` there)."""

    legal_name: str | None = None
    country_code: str | None = None
    company_roles: list[str] = []
    submitted_at: str | None = None


class FirstApproval(ApiModel):
    approved_by: str
    approved_at: str
    comment: str | None = None
    four_eyes_reasons: list[FourEyesCase]


class Decision(ApiModel):
    decided_at: str
    comment: str | None = None
    decided_by: str | None = None
    auto_approved: bool


class Closure(ApiModel):
    closed_at: str
    reason: ClosureReason


class ReviewCaseFields(ApiModel):
    """Fields that the review case and its summary share."""

    id: Uuid
    application_id: str
    company_id: str
    kind: Kind
    verification: Verification
    status: Status
    opened_at: str


class ReviewCase(ReviewCaseFields):
    existing_company: bool
    applicant_sub: str | None
    csp_bpn: str | None = None
    checks: list[ReviewCheck]
    first_approval: FirstApproval | None = None
    decision: Decision | None = None
    closure: Closure | None = None
    application: dict[str, Any] | None = None   # only GET /review-cases/{id}: the application of C1-M2 unchanged


class ReviewCaseSummary(ReviewCaseFields):
    decided_at: str | None = None
    check_counts: CheckCounts
    application: ApplicationBrief | None = None


ReviewCasePage = Page[ReviewCaseSummary]


class ReviewStatusInfo(ApiModel):
    review_case_id: Uuid
    application_id: str
    status: Status
    decided_at: str | None = None


class CloseReviewResult(ApiModel):
    review_case_id: Uuid
    application_id: str
    status: Status


class OpenReviewResult(CloseReviewResult):
    checks: list[CheckOutcome]

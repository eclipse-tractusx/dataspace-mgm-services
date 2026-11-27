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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""The views of an application (`Application`, `ApplicationWithReview`, `ApplicationInternal`,
`ApplicationSummary`), built from its row. Internal fields (the JWT, the declared data, the consent records)
never reach a view.
"""
from __future__ import annotations

from typing import Any

from features.registration.managers import neighbour_client
from features.registration.models.applications import (
    Application,
    ApplicationInternal,
    ApplicationSummary,
    ApplicationWithReview,
)
from features.registration.models.tables import ApplicationRow
from features.registration.models.value_sets import ApplicationStatus
from features.registration.services import attestation_verifier
from portal_common.models import ApiModel
from portal_common.problems import Problem


def _fields(a: ApplicationRow, view: type[ApiModel]) -> dict[str, Any]:
    """The columns of the row that the view has; `attestation` is the stored extract, cut down by the view."""
    return {name: getattr(a, name) for name in view.model_fields if hasattr(a, name)}


def public(a: ApplicationRow) -> Application:
    """`Application`: without the JWT and with the extract of the attestation only."""
    return Application.model_validate(_fields(a, Application))


def summary(a: ApplicationRow) -> ApplicationSummary:
    """`ApplicationSummary`."""
    return ApplicationSummary(id=a.id, company_id=a.company_id, kind=a.kind, existing_company=a.existing_company,
                              verification=a.verification, status=a.status, legal_name=a.company_data["legalName"],
                              country_code=a.company_data["address"].get("countryCode"),
                              company_roles=a.company_roles, created_at=a.created_at, submitted_at=a.submitted_at)


def _review_status(a: ApplicationRow) -> str:
    """`reviewStatus` of 7.4: NONE before submission, UNKNOWN when C1-M3 does not answer."""
    if a.status == ApplicationStatus.CREATED:
        return "NONE"
    try:
        return neighbour_client.review_status(a.id) or "NONE"
    except Problem:
        return "UNKNOWN"


def with_review(a: ApplicationRow) -> ApplicationWithReview:
    fields = _fields(a, ApplicationWithReview) | {"review_status": _review_status(a)}
    return ApplicationWithReview.model_validate(fields)


def internal(a: ApplicationRow) -> ApplicationInternal:
    """`ApplicationInternal` (9.1): the whole attestation with a fresh signature check."""
    detail = None
    if a.attestation and a.attestation_token:
        check = attestation_verifier.signature_check(a.attestation_token)
        detail = a.attestation | {"signatureCheck": check}
    return ApplicationInternal.model_validate(_fields(a, ApplicationInternal) | {"attestation": detail})

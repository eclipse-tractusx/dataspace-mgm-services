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
"""Response models of company roles (README 7.7 to 7.9, 9.4)."""
from __future__ import annotations

from features.company_profile.models.value_sets import ConsentStatus
from portal_common.models import ApiModel


class AgreementConsent(ApiModel):
    """A term a role needs (from C1-M2) with the company's consent to it."""

    agreement_key: str
    version: str | None = None
    name: str | None = None
    names: dict[str, str]
    document_url: str | None = None
    consent_status: ConsentStatus | None = None
    consented_version: str | None = None
    consented_at: str | None = None


class CompanyRoleState(ApiModel):
    """`CompanyRoleState` (7.7): a role of the catalogue or of the company, `NONE` if never had."""

    company_role: str
    assignable_by: str | None = None
    status: str
    description: str
    agreements: list[AgreementConsent]


class CompanyRoleDefinition(ApiModel):
    """`CompanyRoleDefinition` (9.4): a role of the catalogue with its descriptions."""

    company_role: str
    assignable_by: str | None = None
    description: str | None = None
    descriptions: dict[str, str]

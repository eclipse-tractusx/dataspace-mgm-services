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
"""Models of the reference data and the terms (spec C1-M2 openapi.yaml): the form data of 7.1 and the agreement
versions of 7.15, 7.16 and 9.3.
"""
from __future__ import annotations

from pydantic import StrictBool

from features.registration.models.value_sets import AgreementParty, AgreementScope, AgreementStatus
from portal_common.models import ApiModel


class Country(ApiModel):
    code: str
    name: str


class IdentifierTypeInfo(ApiModel):
    type: str
    name: str
    pattern: str | None = None


class CompanyRoleInfo(ApiModel):
    role: str
    name: str
    description: str
    agreement_keys: list[str]


class LocalizedText(ApiModel):
    de: str
    en: str


class AgreementFields(ApiModel):
    """What a version of terms says, shared by the request of 7.16 and the stored `AgreementVersion`."""
    agreement_key: str
    version: str
    party: AgreementParty
    scope: AgreementScope
    title: LocalizedText
    document_urls: dict[str, str]
    reconsent_required: StrictBool
    reconsent_due_at: str | None = None


class AgreementVersionCreate(AgreementFields):
    """`AgreementVersionCreate` (7.16), after `agreement_service.check_agreement`."""
    company_roles: list[str] | None = None


class AgreementVersion(AgreementFields):
    """`AgreementVersion` (README 6.8)."""
    company_roles: list[str]
    status: AgreementStatus
    created_at: str
    created_by: str | None = None


class Agreement(ApiModel):
    """`Agreement`: the active version for the form, title in the requested language (7.1)."""
    agreement_key: str
    version: str
    party: AgreementParty
    scope: AgreementScope
    title: str
    document_urls: dict[str, str]
    company_roles: list[str]

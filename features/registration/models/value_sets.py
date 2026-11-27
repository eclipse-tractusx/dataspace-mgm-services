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
"""Value sets of the registration API (spec C1-M2 openapi.yaml), as `str` enums so that table columns, query
parameters and JSON share one definition.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

Lang = Literal["de", "en"]


class ApplicationStatus(StrEnum):
    """`ApplicationStatus`: CREATED and SUBMITTED are open, the others final (README 6.1)."""
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    WITHDRAWN = "WITHDRAWN"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"


OPEN_STATUSES = (ApplicationStatus.CREATED, ApplicationStatus.SUBMITTED)


class ApplicationKind(StrEnum):
    ONBOARDING = "ONBOARDING"
    REACTIVATION = "REACTIVATION"
    TRANSFER = "TRANSFER"


class Verification(StrEnum):
    EBW = "EBW"
    DOCUMENTS = "DOCUMENTS"


class IdentifierType(StrEnum):
    EUID = "EUID"
    EBWOID = "EBWOID"
    COMMERCIAL_REG_NUMBER = "COMMERCIAL_REG_NUMBER"
    VAT_ID = "VAT_ID"
    LEI_CODE = "LEI_CODE"
    EORI = "EORI"


class DocumentType(StrEnum):
    COMMERCIAL_REGISTER_EXTRACT = "COMMERCIAL_REGISTER_EXTRACT"
    POWER_OF_ATTORNEY = "POWER_OF_ATTORNEY"
    OTHER = "OTHER"


class AgreementStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AgreementParty(StrEnum):
    OSP = "OSP"
    DATASPACE = "DATASPACE"


class AgreementScope(StrEnum):
    ALL = "ALL"
    COMPANY_ROLE = "COMPANY_ROLE"


ReviewStatus = Literal["NONE", "OPEN", "AWAITING_SECOND_APPROVAL", "APPROVED", "DECLINED", "CLOSED", "UNKNOWN"]
SignatureResult = Literal["VALID", "INVALID", "UNAVAILABLE"]

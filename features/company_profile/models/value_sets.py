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
"""Value sets of the company profile (spec C3-M1 openapi.yaml and README 5).

`StrEnum`, so a member is the plain string in JSON, in the database and in comparisons with the
strings the services and neighbours pass around.
"""
from __future__ import annotations

from enum import StrEnum


class CompanyStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    INACTIVE = "INACTIVE"


class DeactivationReason(StrEnum):
    MANUAL = "MANUAL"
    TRANSFERRED = "TRANSFERRED"


class CoreDataSource(StrEnum):
    EBW = "EBW"
    MANUAL = "MANUAL"


class IdentifierType(StrEnum):
    EUID = "EUID"
    EBWOID = "EBWOID"
    VAT_ID = "VAT_ID"
    COMMERCIAL_REG_NUMBER = "COMMERCIAL_REG_NUMBER"
    LEI_CODE = "LEI_CODE"
    EORI = "EORI"


class IdentifierSource(StrEnum):
    BUSINESS_WALLET = "BUSINESS_WALLET"
    DECLARED = "DECLARED"


class RoleStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class RoleSourceKind(StrEnum):
    APPLICATION = "APPLICATION"
    COMPANY = "COMPANY"
    SEED = "SEED"


class ConsentSourceKind(StrEnum):
    APPLICATION = "APPLICATION"
    COMPANY = "COMPANY"


class ConsentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ChangeRequestStatus(StrEnum):
    OPEN = "OPEN"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"


class MediaType(StrEnum):
    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"


def values(enum: type[StrEnum]) -> tuple[str, ...]:
    """The allowed strings of a value set, for membership checks and error messages."""
    return tuple(member.value for member in enum)

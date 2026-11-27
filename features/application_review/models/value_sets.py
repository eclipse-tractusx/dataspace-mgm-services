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
"""Value sets of C1-M3 (openapi.yaml, README 4, 6.2, 6.6) and the spec id. `StrEnum`, so a member is the plain
string of the spec in JSON, in the database and in comparisons."""
from __future__ import annotations

from enum import StrEnum

MODULE = "c1-m3"


class Status(StrEnum):
    OPEN = "OPEN"
    AWAITING_SECOND_APPROVAL = "AWAITING_SECOND_APPROVAL"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    CLOSED = "CLOSED"


class Kind(StrEnum):
    ONBOARDING = "ONBOARDING"
    REACTIVATION = "REACTIVATION"
    TRANSFER = "TRANSFER"


class Verification(StrEnum):
    EBW = "EBW"
    DOCUMENTS = "DOCUMENTS"


class CheckKey(StrEnum):
    ATTESTATION_VALID = "ATTESTATION_VALID"
    REPRESENTATION_CONFIRMED = "REPRESENTATION_CONFIRMED"
    COMPANY_DATA_MATCH = "COMPANY_DATA_MATCH"
    NO_DUPLICATE = "NO_DUPLICATE"
    CSP_MATCH_EXPECTED = "CSP_MATCH_EXPECTED"
    CONSENTS_COMPLETE = "CONSENTS_COMPLETE"


class CheckResult(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class FourEyesCase(StrEnum):
    CHECK_FAILED = "CHECK_FAILED"
    DOCUMENTS = "DOCUMENTS"
    ALWAYS = "ALWAYS"


class CspOutcome(StrEnum):
    NO_MATCH = "NO_MATCH"
    EXPECTED_MATCH = "EXPECTED_MATCH"
    REGISTERED_HERE = "REGISTERED_HERE"
    REGISTERED_AT_OTHER_OSP = "REGISTERED_AT_OTHER_OSP"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    NAME_MATCH_ONLY = "NAME_MATCH_ONLY"
    BPN_MISMATCH = "BPN_MISMATCH"


class ClosureReason(StrEnum):
    WITHDRAWN = "WITHDRAWN"


CHECK_ORDER: list[str] = [key.value for key in CheckKey]
"""The checks in the order of README 6.2; responses list them in this order."""
FOUR_EYES = {case.value for case in FourEyesCase}
AUTO_KINDS = {Kind.ONBOARDING.value, Kind.TRANSFER.value}   # REACTIVATION is never approved automatically (6.6)
IN_REVIEW = (Status.OPEN, Status.AWAITING_SECOND_APPROVAL)

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
"""Value sets of the credentials (openapi.yaml `components/schemas`): credential types, statuses, routes."""
from __future__ import annotations

from enum import StrEnum


class CredentialType(StrEnum):
    BPN = "BPN"
    MEMBERSHIP = "MEMBERSHIP"


class CredentialStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ISSUED = "ISSUED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVOCATION_PENDING = "REVOCATION_PENDING"
    REVOKED = "REVOKED"


class Route(StrEnum):
    """README 6.3: own issuer of the OSP (`CREDENTIAL_ISSUER`, `ISSUER_SERVICE`), CSP issuer, built-in stand-in."""
    CREDENTIAL_ISSUER = "CREDENTIAL_ISSUER"
    ISSUER_SERVICE = "ISSUER_SERVICE"
    CSP_ISSUER = "CSP_ISSUER"
    STUB = "STUB"


class RunStatus(StrEnum):
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RevocationReason(StrEnum):
    COMPANY_DEACTIVATED = "COMPANY_DEACTIVATED"
    OTHER = "OTHER"


class ReportStatus(StrEnum):
    """`status` of a status report of an issuer (README 7.4)."""
    SUCCESSFUL = "SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"


TYPES = tuple(CredentialType)                       # in the order of the spec, also the order of the views
CREDENTIAL_KINDS = ("bpn", "membership")            # `credentialKind` of the callback path
BPN_PATTERN = r"^[Bb][Pp][Nn][Ll][A-Za-z0-9]{12}$"  # openapi.yaml `Bpn` (any case; stored in upper case)

CREDENTIAL_ISSUER, ISSUER_SERVICE, CSP_ISSUER, STUB = (Route.CREDENTIAL_ISSUER, Route.ISSUER_SERVICE,
                                                       Route.CSP_ISSUER, Route.STUB)
# README 6.3 rule 4: the issuance mode of the wallet each route fits
FITS: dict[str, str] = {CREDENTIAL_ISSUER: "ISSUER_WRITES", ISSUER_SERVICE: "HOLDER_REQUESTS",
                        CSP_ISSUER: "HOLDER_REQUESTS"}

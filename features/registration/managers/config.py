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
"""Configuration of the registration (README 4, 14): every variable is read here, at call time and never at
import (AGENTS.md rule 6), so tests and installations can change it while the process runs. An unset value
takes the column "Example" of README 4 (FRAMEWORK 4.8).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

_DURATION = re.compile(r"^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
_DURATION_UNITS = (604800, 86400, 3600, 60, 1)


@dataclass(frozen=True)
class AttestationConfig:
    """The variables `ATTESTATION_*` of README 4 for the checks of 6.4."""
    issuer: str
    audience: str
    algorithms: list[str]
    clients: list[str]
    max_age: int
    skew: int
    cache_seconds: int


def _list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in (os.environ.get(name) or default).split(",") if x.strip()]


def duration_seconds(value: str) -> int:
    """ISO 8601 duration in seconds; raises ValueError for anything else."""
    m = _DURATION.match(value or "")
    if not m or not any(m.groups()):
        raise ValueError(f"ATTESTATION_MAX_AGE: not an ISO 8601 duration: {value!r}")
    return sum(int(g or 0) * unit for g, unit in zip(m.groups(), _DURATION_UNITS, strict=True))


def attestation() -> AttestationConfig:
    """An invalid `ATTESTATION_MAX_AGE` raises ValueError, which stops the start (README 4)."""
    return AttestationConfig(issuer=os.environ.get("ATTESTATION_ISSUER", ""),
                             audience=os.environ.get("ATTESTATION_AUDIENCE") or "portal-registration",
                             algorithms=_list("ATTESTATION_ALGORITHMS", "ES256"),
                             clients=_list("ATTESTATION_CLIENT_IDS"),
                             max_age=duration_seconds(os.environ.get("ATTESTATION_MAX_AGE") or "P30D"),
                             skew=int(os.environ.get("ATTESTATION_CLOCK_SKEW_SECONDS") or 60),
                             cache_seconds=int(os.environ.get("ATTESTATION_JWKS_CACHE_SECONDS") or 300))


def jwks_file() -> str | None:
    """A local JWKS of the issuer (tests, demo); read on every check, never cached."""
    return os.environ.get("ATTESTATION_JWKS_FILE") or None


def jwks_url(issuer: str) -> str:
    return os.environ.get("ATTESTATION_JWKS_URL") or f"{issuer.rstrip('/')}/jwks"


def documents_enabled() -> bool:
    """`DOCUMENTS_ENABLED`: the verification path without Business Wallet (6.9)."""
    return os.environ.get("DOCUMENTS_ENABLED", "true").lower() != "false"


def document_max_bytes() -> int:
    return int(os.environ.get("DOCUMENT_MAX_BYTES") or 10485760)


def document_max_count() -> int:
    return int(os.environ.get("DOCUMENT_MAX_COUNT") or 10)


def catalog_file() -> str | None:
    """`CATALOG_FILE` with company roles and terms (14.3); without it the shared catalogue of `testdata/`."""
    return os.environ.get("CATALOG_FILE") or None


def stub_file(variable: str) -> str:
    """`STUB_COMPANIES_FILE` / `STUB_REVIEWS_FILE` of the built-in stand-ins (14.5), empty if not set."""
    return os.environ.get(variable, "")

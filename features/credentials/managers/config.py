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
"""Configuration of the credentials (README 4), read from the environment at call time and never at import
(AGENTS.md rule 6). The defaults are listed in OPEN-QUESTIONS.md (decision 3)."""
from __future__ import annotations

import datetime as dt
import os

from portal_common import settings


def onboarding_types() -> list[str]:
    raw = os.environ.get("ONBOARDING_CREDENTIAL_TYPES") or "BPN,MEMBERSHIP"
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def resend_after() -> dt.timedelta:
    try:
        return dt.timedelta(hours=float(os.environ.get("RESEND_AFTER_HOURS") or 24))
    except ValueError:
        return dt.timedelta(hours=24)


def issuer_mode() -> str:
    """`ISSUER_MODE`: `OWN` (default) or `CSP`."""
    return os.environ.get("ISSUER_MODE", "OWN")


def csp_issuer_configured() -> bool:
    return bool(os.environ.get("CSP_ISSUER_URL"))


def issuer_routes_configured() -> bool:
    return bool(os.environ.get("ISSUER_ROUTES", "").strip())


def issuer_routes() -> dict[str, str]:
    """`ISSUER_ROUTES`: `SAP_DIV:CREDENTIAL_ISSUER,IDENTITY_HUB:ISSUER_SERVICE,...` as a dict."""
    out = {}
    for part in os.environ.get("ISSUER_ROUTES", "").split(","):
        if ":" in part:
            provider, route = part.split(":", 1)
            out[provider.strip()] = route.strip()
    return out


def stub_issuer_delay() -> float:
    """`STUB_ISSUER_DELAY_SECONDS` (default 1, never negative)."""
    try:
        return max(0.0, float(os.environ.get("STUB_ISSUER_DELAY_SECONDS", "1")))
    except ValueError:
        return 1.0


def stub_issuer_fail_types() -> set[str]:
    """`STUB_ISSUER_FAIL_TYPES`: credential types the stand-in declines."""
    return {t.strip().upper() for t in os.environ.get("STUB_ISSUER_FAIL_TYPES", "").split(",") if t.strip()}


# --------------------------------------------------------------------------- issuer routes (README 11.3 to 11.5)
def callback_base_url() -> str:
    """`CALLBACK_BASE_URL`, else the address of the installation."""
    return (os.environ.get("CALLBACK_BASE_URL") or settings.base_url()).rstrip("/")


def _definitions(variable: str, default: str = "BPN:bpn,MEMBERSHIP:membership") -> dict[str, str]:
    """`<TYPE>:<identifier>,...` of `variable` (or `default`) as a dict keyed by the credential type."""
    out = {}
    for part in (os.environ.get(variable) or default).split(","):
        if ":" in part:
            t, ident = part.split(":", 1)
            out[t.strip().upper()] = ident.strip()
    return out


def csp_issuer_definitions() -> dict[str, str]:
    """`CSP_ISSUER_CREDENTIAL_DEFINITIONS`: credential type -> identifier at the CSP issuer."""
    return _definitions("CSP_ISSUER_CREDENTIAL_DEFINITIONS")


def issuer_service_definitions() -> dict[str, str]:
    """`ISSUER_SERVICE_CREDENTIAL_DEFINITIONS`: credential type -> credential definition at the IssuerService."""
    return _definitions("ISSUER_SERVICE_CREDENTIAL_DEFINITIONS")


def credential_format() -> str:
    return os.environ.get("CREDENTIAL_FORMAT") or "VC1_0_JWT"


def csp_issuer_url() -> str:
    return os.environ.get("CSP_ISSUER_URL", "")


def csp_issuer_did() -> str:
    return os.environ.get("CSP_ISSUER_DID") or "did:web:issuer.csp.example.org"


def credential_issuer_url() -> str:
    return os.environ.get("CREDENTIAL_ISSUER_URL", "").rstrip("/")


def credential_issuer_token_request() -> tuple[str, dict[str, str]]:
    """Token endpoint of the Credential Issuer and the form of the client credentials grant."""
    return os.environ.get("CREDENTIAL_ISSUER_TOKEN_URL", ""), {
        "grant_type": "client_credentials",
        "client_id": os.environ.get("CREDENTIAL_ISSUER_CLIENT_ID", ""),
        "client_secret": os.environ.get("CREDENTIAL_ISSUER_CLIENT_SECRET", "")}


def issuer_service_admin_url() -> str:
    """Administration interface of the own IssuerService for its participant (default `issuer`)."""
    pid = os.environ.get("ISSUER_SERVICE_PARTICIPANT_ID") or "issuer"
    return os.environ.get("ISSUER_SERVICE_ADMIN_URL", "").rstrip("/") + f"/api/admin/participants/{pid}"


def issuer_service_api_key() -> str:
    return os.environ.get("ISSUER_SERVICE_API_KEY", "")


def issuer_did() -> str:
    """`ISSUER_DID`: DID of the own IssuerService."""
    return os.environ.get("ISSUER_DID", "")

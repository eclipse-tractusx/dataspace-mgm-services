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
"""Reference data of C1-M2, read-only: countries and identifier types from `masterDataFile` (FRAMEWORK 4.8),
company roles and the initial terms from `CATALOG_FILE` (README 14.3), by default the shared catalogue of
`testdata/`. The terms are state and live in the table of `agreement_repository`; this module only gives their
initial values. Files are read once per path and indexed by key.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

from features.registration.managers import config
from portal_common import settings
from tools import testdata

INITIAL_AT = "2026-01-01T00:00:00Z"
UPPER_CASE_IDENTIFIERS = ("EUID", "VAT_ID", "LEI_CODE", "EORI")
# README 14.3; the agreements of a role come from the catalogue
ROLES = [
    {"role": "ACTIVE_PARTICIPANT", "selectable": True, "name": {"de": "Teilnehmer", "en": "Participant"},
     "description": {"de": "Datenanbieter, Datenkonsument, App-Nutzer",
                     "en": "Data provider, data consumer, app user"}},
    {"role": "APP_PROVIDER", "selectable": True, "name": {"de": "App-Anbieter", "en": "App provider"},
     "description": {"de": "bietet Apps im Marktplatz an", "en": "offers apps in the marketplace"}},
    {"role": "SERVICE_PROVIDER", "selectable": True, "name": {"de": "Service-Anbieter", "en": "Service provider"},
     "description": {"de": "bietet Services im Marktplatz an", "en": "offers services in the marketplace"}},
    {"role": "ONBOARDING_SERVICE_PROVIDER", "selectable": False,
     "name": {"de": "Onboarding-Dienstleister", "en": "Onboarding service provider"},
     "description": {"de": "Unternehmen des OSP", "en": "Company of the OSP"}},
]


@functools.lru_cache(maxsize=4)
def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reset() -> None:
    """Read the files again (a test or an installation changed them)."""
    _read.cache_clear()
    _master_index.cache_clear()


# ----------------------------------------------------------------------- roles and terms (14.3)
def roles() -> list[dict]:
    path = config.catalog_file()
    return _read(path)["companyRoles"] if path else ROLES


def selectable(role: str) -> bool:
    return any(r["role"] == role and r.get("selectable") for r in roles())


def initial_agreements() -> list[dict]:
    """The initial versions of the terms (README 5), as the fields of `AgreementVersionRow`."""
    path = config.catalog_file()
    if not path:
        return [_version(x) for x in testdata.agreements()]
    data = _read(path)
    return [_version({**x, "agreementKey": x["key"],
                      "companyRoles": [r["role"] for r in data["companyRoles"] if x["key"] in r.get("agreements", [])]})
            for x in data["agreements"]]


def _version(x: dict) -> dict:
    return {"agreement_key": x["agreementKey"], "version": x["version"], "party": x["party"], "scope": x["scope"],
            "company_roles": list(x.get("companyRoles") or []), "title": x["title"], "document_urls": x["documentUrls"],
            "status": "ACTIVE", "reconsent_required": False, "reconsent_due_at": None, "created_at": INITIAL_AT,
            "created_by": None}


# --------------------------------------------------------------- countries and identifiers (6.6)
def master() -> dict:
    return _read(str(settings.resolve_path(settings.get("masterDataFile"))))


@functools.lru_cache(maxsize=4)
def _master_index(path: str) -> tuple[dict[str, dict], dict[str, dict]]:
    data = _read(path)
    return {c["code"]: c for c in data["countries"]}, {t["type"]: t for t in data["identifierTypes"]}


def _index() -> tuple[dict[str, dict], dict[str, dict]]:
    return _master_index(str(settings.resolve_path(settings.get("masterDataFile"))))


def country(code: object) -> dict | None:
    """The country with this code, None if unknown (also for a code that is not text, e.g. from a token)."""
    return _index()[0].get(code) if isinstance(code, str) else None


def identifier_pattern(type_: str, code: str) -> str | None:
    """Regular expression per country, otherwise `Worldwide` (6.6)."""
    patterns = (_index()[1].get(type_) or {}).get("patterns", {})
    return patterns.get(code) or patterns.get("Worldwide")


def identifier_error(type_: str, value: str, code: str) -> str | None:
    """Why this identifier is not allowed for this country (6.6), or None."""
    c = country(code)
    if c is None or type_ not in c.get("identifierTypes", []):
        return f"identifier type {type_} is not allowed for country {code}"
    pattern = identifier_pattern(type_, code)
    if pattern and not re.fullmatch(pattern, value):
        return f"{type_} has an invalid format for country {code}"
    if type_ == "EUID" and value[:2] != code:
        return "EUID must start with the country of the company"
    return None


def normalise_identifier(type_: str, value: str) -> str:
    """6.6: whitespace removed at both ends; `EUID`, `VAT_ID`, `LEI_CODE`, `EORI` in upper case."""
    value = value.strip()
    return value.upper() if type_ in UPPER_CASE_IDENTIFIERS else value

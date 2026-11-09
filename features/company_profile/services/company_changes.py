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
"""What a change of core data changes (README 6.3, 7.2, 7.4): changed fields, merge with validation,
identifier comparison and conflicts with the business wallet. Used by company changes and change requests.
"""
from __future__ import annotations

from features.company_profile.managers import company_repository
from features.company_profile.services import company_validation

# ------------------------------------------------------------------------ change by people (7.2)
CORE_TEXT_FIELDS = ("name", "street", "house_number", "address_addition", "postal_code", "city",
                    "region", "country_code")
CAMEL = {snake: camel for camel, snake in company_validation.ALIASES.items()}


def changed_fields(row: dict, body: dict, identifiers: list[dict] | None) -> list[str]:
    """Names of the fields the body really changes, camelCase, for the event (README 7.2, 7.12)."""
    changed = []
    for key, value in body.items():
        field = company_validation.field_name(key)
        if field in CORE_TEXT_FIELDS or field == "short_name":
            before, after = row.get(field), value
            if (before or "") != (after or "") and not (
                    before and after and company_validation.same_value(before, after)):
                changed.append(CAMEL.get(field, field))
    if identifiers is not None:
        before = {(entry["type"], entry["value_normalized"]) for entry in company_repository.list_identifiers(row["id"])}
        after = {(entry["type"], company_validation.value_normalized(entry["value"])) for entry in identifiers}
        if before != after:
            changed.append("identifiers")
    return changed


def validate_merge(row: dict, body: dict) -> dict:
    """The row after the body, flat, so the merged state is validated, not only the patch."""
    merged = {field: row.get(field) for field in row}
    merged.update(company_validation.flat_fields(body))
    return merged


def identifiers_from(body: dict) -> list[dict] | None:
    if "identifiers" not in body:
        return None
    return [{"type": entry.get("type"), "value": entry.get("value"),
             "source": entry.get("source") or "DECLARED"} for entry in body.get("identifiers") or []]


CORE_IDENTIFIERS = ("EUID", "EBWOID")


def differs_field(row: dict, key: str, value) -> bool:
    """`True` if this part of a request differs from the current state (7.4 point 5/6)."""
    if key == "address":
        return any(not company_validation.same_value(row.get(field), entry)
                   for field, entry in company_validation.flat_fields({"address": value}).items())
    return not company_validation.same_value(row.get(company_validation.field_name(key)), value)


def _differs_identifiers(row: dict, identifiers: list[dict]) -> bool:
    """Compare with the declared identifiers only; wallet identifiers are not part of a request."""
    before = {(entry["type"], entry["value_normalized"])
              for entry in company_repository.list_identifiers(row["id"])
              if entry["source"] != "BUSINESS_WALLET"}
    after = {(entry["type"], company_validation.value_normalized(entry["value"])) for entry in identifiers}
    return before != after


def changes_differs(row: dict, changes: dict) -> bool:
    """`True` if any part of the request differs from the current company (7.4 point 6)."""
    for key, value in changes.items():
        if key == "identifiers":
            if _differs_identifiers(row, value):
                return True
        elif differs_field(row, key, value):
            return True
    return False


def wallet_identifier_conflict(row: dict, identifiers: list[dict]) -> list[dict]:
    """Identifiers of the list whose stored source is `BUSINESS_WALLET` (400, 7.4 point 4, 7.12 point 3)."""
    stored = {entry["type"] for entry in company_repository.list_identifiers(row["id"])
              if entry["source"] == "BUSINESS_WALLET"}
    return [{"field": f"identifiers.{entry.get('type')}", "reason": "source BUSINESS_WALLET"}
            for entry in identifiers if entry.get("type") in stored]


def identifier_core_changed(row: dict, identifiers: list[dict]) -> bool:
    """A changed, added or dropped declared EUID/EBWOID is a change of core data (6.3).

    A wallet identifier that stays outside the request list is not a change.
    """
    stored = {entry["type"]: entry["value"] for entry in company_repository.list_identifiers(row["id"])
              if entry["type"] in CORE_IDENTIFIERS and entry["source"] != "BUSINESS_WALLET"}
    now = {entry["type"]: entry["value"] for entry in identifiers
           if entry.get("type") in CORE_IDENTIFIERS}
    if set(stored) != set(now):
        return True
    return any(not company_validation.same_value(stored[kind], value) for kind, value in now.items())

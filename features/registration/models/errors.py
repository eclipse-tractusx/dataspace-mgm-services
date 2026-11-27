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
"""The Problem factories of the registration (FRAMEWORK 4.5, README 12): every layer raises the Problems of the
spec through these functions, so type, status and extension members are written once. `parse()` reads a
checked body into its model.
"""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from features.registration.models import MODULE
from portal_common.problems import Problem


def _problem(status: int, name: str, detail: str | None = None, retryable: bool | None = None,
             **ext: object) -> Problem:
    """`retryable` is only a member where the spec gives it (steps, upstream errors)."""
    if retryable is not None:
        ext["retryable"] = retryable
    return Problem(MODULE, status, name, None, detail, **ext)


def field_error(field: str, message: str) -> dict:
    return {"field": field, "message": message}


def validation_problem(errors: list[dict], retryable: bool | None = None) -> Problem:
    return _problem(400, "validation", errors=errors, retryable=retryable)


def parse[M: BaseModel](model: type[M], body: object) -> M:
    """The body as its model, after the checks of the service: what they let through but the types of the spec
    do not allow is a validation error like theirs, never a 500."""
    try:
        return model.model_validate(body)
    except ValidationError as e:
        raise validation_problem([field_error(".".join(map(str, err["loc"])) or "body", err["msg"])
                                  for err in e.errors()]) from e


# ------------------------------------------------------------------------------------- generic
def not_found(retryable: bool | None = None) -> Problem:
    return _problem(404, "not-found", retryable=retryable)


def invalid_state(detail: str, retryable: bool | None = None) -> Problem:
    return _problem(409, "invalid-state", detail, retryable=retryable)


def conflict(detail: str) -> Problem:
    return _problem(409, "conflict", detail)


def upstream_error(detail: str, retryable: bool) -> Problem:
    """502: a neighbour or the issuer did not answer usefully."""
    return _problem(502, "upstream-error", detail, retryable=retryable)


# -------------------------------------------------------------------------- applications (12)
def account_bound() -> Problem:
    return _problem(403, "account-bound")


def documents_disabled() -> Problem:
    return _problem(400, "documents-disabled")


def open_application_exists(existing_application_id: str) -> Problem:
    return _problem(409, "open-application-exists", existingApplicationId=existing_application_id)


def company_has_open_application() -> Problem:
    return _problem(409, "company-has-open-application")


def company_unknown() -> Problem:
    """6.2: the referenced company does not exist at C3-M1."""
    return _problem(409, "company-not-eligible", "company unknown")


def company_not_eligible(company_status: str | None) -> Problem:
    """6.2: status and deactivation reason of the company do not fit the application kind."""
    return _problem(409, "company-not-eligible", companyStatus=company_status)


def already_decided(review_status: str) -> Problem:
    return _problem(409, "already-decided", reviewStatus=review_status)


def documents_incomplete(missing_document_types: list[str], declaration_missing: bool) -> Problem:
    return _problem(400, "documents-incomplete", missingDocumentTypes=missing_document_types,
                    representationDeclarationMissing=declaration_missing)


def consents_incomplete(missing: list[dict]) -> Problem:
    return _problem(400, "consents-incomplete", missing=missing)


# --------------------------------------------------------------------------- attestation (6.4)
def attestation_invalid(reason: str) -> Problem:
    return _problem(400, "attestation-invalid", reason=reason)


def attestation_mismatch(fields: list[str]) -> Problem:
    return _problem(400, "attestation-mismatch", fields=fields)


def attestation_used() -> Problem:
    return _problem(409, "attestation-used")


def attestation_expired() -> Problem:
    return _problem(409, "attestation-expired")

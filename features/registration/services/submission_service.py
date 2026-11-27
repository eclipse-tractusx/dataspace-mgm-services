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
"""Submission of an application (README 7.10): the consents to the required terms, the attestation still
usable, and for DOCUMENTS the commercial register extract and the declaration of representation.
"""
from __future__ import annotations

from features.registration.managers import agreement_repository, application_repository
from features.registration.managers.application_repository import applications_lock
from features.registration.models import errors as problems
from features.registration.models.applications import (
    AgreementRef,
    Application,
    Consent,
    ConsentRecord,
    SubmitRequest,
)
from features.registration.models.tables import ApplicationRow
from features.registration.models.value_sets import ApplicationStatus, DocumentType, Verification
from features.registration.services import attestation_verifier
from features.registration.services.application_service import own
from features.registration.services.application_views import public
from features.registration.services.shared import (
    MODULE,
    as_json,
    audit_entry,
    field_error,
    parse,
    utc_now,
    validation_problem,
)
from portal_common import events


def submit_application(application_id: str, sub: str, body: dict) -> Application:
    """7.10; a repetition of a submitted application answers with it unchanged."""
    with applications_lock:
        a = own(sub, application_id)
        if a.status == ApplicationStatus.SUBMITTED:
            return public(a)
        if a.status != ApplicationStatus.CREATED:
            raise problems.invalid_state(f"application is {a.status}")
        request = _checked_request(body)
        _check_proof(a, request)
        required = _check_consents(a, request)
        _record_submission(a, request, required, sub)
        application_repository.save(a, audit=audit_entry(a, "submitApplication", sub=sub))
        events.publish(MODULE, "ApplicationSubmitted", {"applicationId": a.id, "companyId": a.company_id,
                                                        "kind": a.kind, "existingCompany": a.existing_company,
                                                        "applicantSub": sub})
        return public(a)


def _checked_request(body: dict) -> SubmitRequest:
    consents = body.get("consents")
    valid = isinstance(consents, list) and consents and all(
        isinstance(c, dict) and isinstance(c.get("agreementKey"), str) and isinstance(c.get("version"), str)
        and c.get("language") in ("de", "en") for c in consents)
    if not valid:
        raise validation_problem([field_error("consents",
                                              "at least one consent with agreementKey, version and language de or en")])
    return parse(SubmitRequest, body)


def _check_proof(a: ApplicationRow, request: SubmitRequest) -> None:
    """EBW: the attestation is still usable (6.4); DOCUMENTS: extract and declaration are there (6.9)."""
    if a.verification == Verification.EBW and not attestation_verifier.usable_at_submission(a):
        raise problems.attestation_expired()
    if a.verification == Verification.DOCUMENTS:
        types = {d["documentType"] for d in a.documents}
        extract = DocumentType.COMMERCIAL_REGISTER_EXTRACT
        missing_types = [] if extract in types else [str(extract)]
        undeclared = request.representation_declared is not True
        if missing_types or undeclared:
            raise problems.documents_incomplete(missing_types, undeclared)


def _check_consents(a: ApplicationRow, request: SubmitRequest) -> list[AgreementRef]:
    """6.8: exactly the active versions of the required terms; returns them."""
    required = [AgreementRef(agreement_key=x.agreement_key, version=x.version)
                for x in agreement_repository.required(a.company_roles)]
    needed = {(r.agreement_key, r.version) for r in required}
    given = {(c.agreement_key, c.version) for c in request.consents}
    missing = [as_json(r) for r in required if (r.agreement_key, r.version) not in given]
    if missing:
        raise problems.consents_incomplete(missing)
    extra = [c.agreement_key for c in request.consents if (c.agreement_key, c.version) not in needed]
    if extra:
        raise validation_problem([field_error("consents", f"unknown or not required terms: {k}") for k in extra])
    return required


def _record_submission(a: ApplicationRow, request: SubmitRequest, required: list[AgreementRef], sub: str) -> None:
    now = utc_now()
    attestation_id = (a.attestation or {}).get("attestationId")
    a.consents = [as_json(Consent(**c.model_dump(), given_at=now)) for c in request.consents]
    a.consent_records = [as_json(ConsentRecord(**c.model_dump(), given_at=now, given_by_sub=sub,
                                               attestation_id=attestation_id)) for c in request.consents]
    a.required_agreements = [as_json(r) for r in required]
    a.status, a.submitted_at, a.changed_at = ApplicationStatus.SUBMITTED, now, now
    if a.verification == Verification.DOCUMENTS:
        a.representation_declared = True

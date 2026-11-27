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
"""Applications of people (README 7.2 to 7.6, 7.10, 7.11) and the read paths of OSP staff (7.12, 7.13).

The scope `own` is applied here: another person's application answers 404 (README 6.3). A change reads the
application again under `applications_lock` and decides on that state (6.11).
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from features.registration.managers import application_repository, config, neighbour_client, reference_catalog
from features.registration.managers.application_repository import applications_lock
from features.registration.models import errors as problems
from features.registration.models.applications import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationWithReview,
    AttestationRecord,
)
from features.registration.models.tables import ApplicationRow
from features.registration.models.value_sets import OPEN_STATUSES, ApplicationStatus, Verification
from features.registration.services import attestation_verifier
from features.registration.services.application_validation import (
    check_company_fields,
    check_create,
    check_reference_data,
    check_roles,
)
from features.registration.services.application_views import public, summary, with_review
from features.registration.services.company_data import (
    build_company_data,
    check_existing_identifiers,
    company_data_ebw,
    company_for_reference,
    given_identifiers,
    new_company_id,
)
from features.registration.services.shared import (
    ATTESTATION_MAX_CHARS,
    MODULE,
    as_json,
    audit_entry,
    field_error,
    page_of,
    parse,
    utc_now,
    validation_problem,
)
from portal_common import events
from portal_common.models import Page

UPDATABLE = ("legalName", "shortName", "address", "identifiers", "companyRoles")


# ----------------------------------------------------------------------------- read (7.3, 7.12, 7.13)
def own(sub: str, application_id: str) -> ApplicationRow:
    """Scope `own` (6.3): for other people the application does not exist."""
    a = application_repository.get(application_id)
    if not a or a.applicant_sub != sub:
        raise problems.not_found()
    return a


def any_application(application_id: str) -> ApplicationRow:
    a = application_repository.get(application_id)
    if not a:
        raise problems.not_found()
    return a


def get_own_application(sub: str, application_id: str) -> ApplicationWithReview:
    """7.4, scope `own`."""
    return with_review(own(sub, application_id))


def get_any_application(application_id: str) -> ApplicationWithReview:
    """7.13."""
    return with_review(any_application(application_id))


def list_own(sub: str, status: Sequence[str] | None, page: int, size: int) -> Page:
    return page_of(application_repository.search(applicant_sub=sub, statuses=status), page, size, summary)


def list_all(status: Sequence[str] | None, kind: Sequence[str] | None, verification: Sequence[str] | None,
             company_id: str | None, page: int, size: int) -> Page:
    rows = application_repository.search(statuses=status, kinds=kind, verifications=verification, company_id=company_id)
    return page_of(rows, page, size, summary)


def require_created(a: ApplicationRow) -> None:
    """Only an application in status CREATED can be changed (6.1)."""
    if a.status != ApplicationStatus.CREATED:
        raise problems.invalid_state(f"application is {a.status}")


# ------------------------------------------------------------------------------------ create (7.2)
def create_application(body: dict, claims: dict) -> tuple[Application, bool]:
    """7.2, in the order of the README. Returns the application and whether it is new (201) or a repetition (200)."""
    if claims.get("company_id"):
        raise problems.account_bound()
    check_create(body)
    request = parse(ApplicationCreate, body)
    if request.verification == Verification.DOCUMENTS and not config.documents_enabled():
        raise problems.documents_disabled()
    header, payload = (attestation_verifier.verify(request.attestation or "", claims)
                       if request.verification == Verification.EBW else ({}, None))
    sub = claims["sub"]
    with applications_lock:
        if repeated := _check_unique(sub, payload, repetition=True):
            return public(repeated), False
    given = request.company_data.model_dump(by_alias=True, exclude_unset=True) if request.company_data else {}
    company = company_for_reference(request) if (request.company_id or request.bpn) else None
    company_claim = (payload or {}).get("company")
    company_roles = request.company_roles or []
    if company:
        _check_existing_company(company, company_claim, given)
        company_roles = company_roles or _selectable_roles_of(company)
    data, comparison = build_company_data(request.verification, company_claim, given)
    check_reference_data(data, company_roles, request.verification)
    with applications_lock:
        _check_unique(sub, payload, repetition=False)   # concurrent creation: the same answer as above
        if company and application_repository.company_has_open(company["id"]):
            raise problems.company_has_open_application()
        now = utc_now()
        a = ApplicationRow(
            id=str(uuid.uuid4()), seq=application_repository.next_seq(),
            company_id=company["id"] if company else new_company_id((company_claim or {}).get("ebwoid")),
            applicant_sub=sub, status=ApplicationStatus.CREATED, kind=request.kind,
            existing_company=bool(company), verification=request.verification,
            applicant={"sub": sub, "givenName": claims.get("given_name"), "familyName": claims.get("family_name")},
            company_data=data, company_roles=list(company_roles), comparison=comparison, created_at=now,
            changed_at=now, given=given)
        if payload:
            _take_attestation(a, attestation_verifier.summary(header, payload), request.attestation, payload)
        application_repository.save(a, audit=audit_entry(a, "createApplication", sub=sub),
                                    used_jti=payload["jti"] if payload else None)
        events.publish(MODULE, "ApplicationCreated", {"applicationId": a.id, "companyId": a.company_id,
                                                      "kind": a.kind, "existingCompany": a.existing_company})
        return public(a), True


def _check_unique(sub: str, payload: dict | None, repetition: bool) -> ApplicationRow | None:
    """6.11: one open application per person and one application per attestation. With `repetition`, the same
    attestation again answers with the open application (idempotent repetition of 7.2)."""
    existing = application_repository.open_of_applicant(sub)
    if existing:
        same = payload and existing.attestation and existing.attestation["attestationId"] == payload["jti"]
        if repetition and same:
            return existing
        raise problems.open_application_exists(existing.id)
    if payload and application_repository.attestation_used(payload["jti"]):
        raise problems.attestation_used()
    return None


def _check_existing_company(company: dict, company_claim: dict | None, given: dict) -> None:
    """6.2: with a reference, the company of the application must be the existing one."""
    euid = (company_claim or {}).get("euid") or given_identifiers(given).get("EUID")
    check_existing_identifiers(company, (company_claim or {}).get("ebwoid"), euid)


def _selectable_roles_of(company: dict) -> list[str]:
    """6.2: without given roles, the selectable roles of the existing company."""
    roles = [_role_name(r) for r in company.get("companyRoles") or []]
    selectable = [r for r in roles if reference_catalog.selectable(r)]
    if not selectable:
        raise validation_problem([field_error("companyRoles", "the company has no selectable roles: give the roles")])
    return selectable


def _role_name(role: object) -> str:
    """Company roles of C3-M1 come as names or as `{companyRole, status}`."""
    return role.get("companyRole") if isinstance(role, dict) else role  # type: ignore[return-value]


def _take_attestation(a: ApplicationRow, record: AttestationRecord, token: str | None, payload: dict) -> None:
    a.attestation = as_json(record)
    a.attestation_token = token
    a.attestation_claims = {"iat": payload["iat"], "exp": payload["exp"], "company": payload["company"]}


# ------------------------------------------------------------------------------------ change (7.5, 7.6)
def update_application(application_id: str, sub: str, body: dict) -> Application:
    """7.5."""
    a = own(sub, application_id)
    require_created(a)
    change = _checked_change(a, body)
    company_claim = (a.attestation_claims or {}).get("company")
    given = {**a.given, **{k: v for k, v in change.items() if k != "companyRoles"}}
    if "identifiers" in change and a.existing_company:
        _check_existing_company(neighbour_client.company_by_id(a.company_id) or {}, company_claim, given)
    data, comparison = build_company_data(a.verification, company_claim, given)
    roles = change.get("companyRoles", a.company_roles)
    check_reference_data(data, roles, a.verification)
    with applications_lock:
        a = own(sub, application_id)
        require_created(a)
        a.company_data, a.comparison, a.company_roles = data, comparison, list(roles)
        a.changed_at, a.given = utc_now(), given
        application_repository.save(a, audit=audit_entry(a, "updateApplication", sub=sub))
        return public(a)


def _checked_change(a: ApplicationRow, body: dict) -> dict:
    """The fields of 7.5 the body changes, checked like at creation (6.2, 6.9), in their JSON form."""
    change = {k: body[k] for k in UPDATABLE if k in body}
    if not change:
        raise validation_problem([field_error("body", f"at least one of {', '.join(UPDATABLE)}")])
    errors: list[dict] = [field_error(k, "must not be null") for k in ("legalName", "address", "identifiers")
                          if k in change and change[k] is None]
    check_company_fields(change, errors)
    if "companyRoles" in change:
        check_roles(change["companyRoles"], errors)
    if a.verification == Verification.DOCUMENTS and change.get("identifiers") == []:
        errors.append(field_error("identifiers", "at least one identifier for DOCUMENTS"))
    if errors:
        raise validation_problem(errors)
    return parse(ApplicationUpdate, change).model_dump(by_alias=True, exclude_unset=True)


def replace_attestation(application_id: str, claims: dict, token: object) -> Application:
    """7.6."""
    sub = claims["sub"]
    a = own(sub, application_id)
    if a.status != ApplicationStatus.CREATED or a.verification == Verification.DOCUMENTS:
        raise problems.invalid_state("only in status CREATED and the verification path EBW")
    if not (isinstance(token, str) and 0 < len(token) <= ATTESTATION_MAX_CHARS):
        raise validation_problem([field_error("attestation", "required, at most 16 KB")])
    header, payload = attestation_verifier.verify(token, claims)
    if a.attestation and a.attestation["attestationId"] == payload["jti"]:
        return public(a)
    new = payload["company"]
    euid = _check_same_company(a, new)
    data, comparison = company_data_ebw(new, a.given)
    check_reference_data(data, a.company_roles, a.verification)
    if a.existing_company:
        applicant_euid = given_identifiers(a.given).get("EUID")
        check_existing_identifiers(neighbour_client.company_by_id(a.company_id) or {}, new["ebwoid"],
                                   euid or applicant_euid)
    with applications_lock:
        if application_repository.attestation_used(payload["jti"]):
            raise problems.attestation_used()
        a = own(sub, application_id)
        require_created(a)
        a.company_data, a.comparison, a.changed_at = data, comparison, utc_now()
        _take_attestation(a, attestation_verifier.summary(header, payload), token, payload)
        application_repository.save(a, audit=audit_entry(a, "replaceAttestation", sub=sub), used_jti=payload["jti"])
        return public(a)


def _check_same_company(a: ApplicationRow, new: dict) -> str | None:
    """7.6: the new attestation is about the same company; returns its normalised EUID."""
    old = (a.attestation_claims or {}).get("company") or {}
    fields = [name for name, key in (("EBWOID", "ebwoid"), ("COUNTRY", "country")) if new[key] != old.get(key)]
    applicant_euid = given_identifiers(a.given).get("EUID")
    euid = reference_catalog.normalise_identifier("EUID", new["euid"]) if new.get("euid") else None
    if euid and ((old.get("euid") and reference_catalog.normalise_identifier("EUID", old["euid"]) != euid)
                 or (applicant_euid and applicant_euid != euid)):
        fields.append("EUID")
    if fields:
        raise problems.attestation_mismatch(fields)
    return euid


# --------------------------------------------------------------------------------- withdraw (7.11)
def withdraw_application(application_id: str, sub: str) -> Application:
    """7.11."""
    a = own(sub, application_id)
    _require_withdrawable(a)
    if a.status == ApplicationStatus.SUBMITTED:
        review = neighbour_client.review_status(a.id)   # not reachable: 502, nothing changed
        if review in ("APPROVED", "DECLINED"):
            raise problems.already_decided(review)
    with applications_lock:
        a = own(sub, application_id)
        if a.status == ApplicationStatus.WITHDRAWN:
            return public(a)
        _require_withdrawable(a)
        submitted = a.status == ApplicationStatus.SUBMITTED
        now = utc_now()
        a.status, a.withdrawn_at, a.changed_at = ApplicationStatus.WITHDRAWN, now, now
        application_repository.save(a, audit=audit_entry(a, "withdrawApplication", sub=sub))
        if submitted:
            events.publish(MODULE, "ApplicationWithdrawn", {"applicationId": a.id, "companyId": a.company_id,
                                                            "kind": a.kind, "existingCompany": a.existing_company})
        return public(a)


def _require_withdrawable(a: ApplicationRow) -> None:
    if a.status not in (*OPEN_STATUSES, ApplicationStatus.WITHDRAWN):
        raise problems.invalid_state(f"application is {a.status}")

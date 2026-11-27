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
#  Assisted-By: Claude Code (claude-fable-5-2)
#################################################################################
"""Acceptance of an invitation with a mandate (C2-M2 README 6.8a, 7.10): the person shows a verification
attestation of the EBW-Connector with the purpose `representation` instead of the invitation code.

`InvitationServiceImpl`, `AttestationCheck`, `DaoService` and `Context` are real; the invitation table is a list,
the Portal IAM, C3-M1 and the binding of the account (`UserServiceImpl.bind`) are mocks."""
from __future__ import annotations

import datetime as dt
import json
import time
from unittest.mock import MagicMock, create_autospec

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from features.app_access.managers.config import Config
from features.app_access.managers.dao import (
    AppClientTemplateDao,
    AppInstanceClientDao,
    AuditLogDao,
    CompanyDao,
    CompanyUserDao,
    DaoService,
    InvitationDao,
    RoleAssignmentLogDao,
)
from features.app_access.managers.gateways import AttestationKeysImpl, CompanyProfileGatewayImpl
from features.app_access.managers.ports import (
    AttestationKeys,
    CompanyProfileGateway,
    Database,
    PortalIam,
    SubscriptionsGateway,
)
from features.app_access.models.constants import CompanyStatus, InvitationKind, InvitationStatus, JoinedVia
from features.app_access.models.exception import (
    AttestationInvalidException,
    CompanyNotActiveException,
    InvitationNotFoundException,
    NameMismatchException,
    RepresentationNotConfirmedException,
    UserAlreadyBoundException,
    ValidationException,
)
from features.app_access.models.exception_translator import ExceptionTranslator
from features.app_access.models.internal import Company, CompanyUser, Invitation, InvitationCode, now
from features.app_access.services.context import Context
from features.app_access.services.invitation_service_impl import InvitationServiceImpl
from features.app_access.services.user_service_impl import UserServiceImpl

# Test data of FRAMEWORK 7a and C5-M1 14.5
MASCHINENBAU, EBWOID = "c0000001-0000-4000-8000-000000000001", "EBWOID-DE-0000000001"
ERIKA, MAX = "5a1c0001-0000-4000-8000-000000000001", "5a1c0002-0000-4000-8000-000000000002"
ISSUER, KID = "https://ebw-connector.example.org", "connector-1"
KEY = ec.generate_private_key(ec.SECP256R1())
JWK = {**json.loads(jwt.algorithms.ECAlgorithm.to_jwk(KEY.public_key())), "kid": KID}
MAX_CLAIMS = {"sub": MAX, "given_name": "Max", "family_name": "Beispiel"}


def attestation(key: ec.EllipticCurvePrivateKey = KEY, typ: str = "ebw-attestation+jwt", **changes) -> str:
    """A verification attestation as the EBW-Connector issues it without the company step (C5-M1 9.1)."""
    at = int(time.time())
    payload = {
        "iss": ISSUER, "sub": EBWOID, "aud": "portal-registration", "iat": at, "exp": at + 3600,
        "jti": "0d0a5e0e-3c4b-4f4e-9d53-2f6f3a1b7c10", "attestation_version": "0.2", "purpose": "representation",
        "verified_at": at, "client_id": "osp-a-ui",
        "person": {"given_name": "Max", "family_name": "Beispiel"},
        "company": {"legal_name": "Beispiel Maschinenbau GmbH", "ebwoid": EBWOID, "country": "DE"},
        "representation": {"confirmed": True, "result": "CONFIRMED", "type": "power_of_attorney", "role": "Purchasing",
                           "company_id": EBWOID, "trust": "company_credential"},
    }
    payload.update(changes)
    return jwt.encode({k: v for k, v in payload.items() if v is not None}, key, algorithm="ES256",
                      headers={"typ": typ, "kid": KID})


class Invitations(InvitationDao):
    """The table `invitation` as a list."""

    def __init__(self) -> None:
        self.rows: dict[str, Invitation] = {}

    def lock(self, invitation_id: str):
        return MagicMock()

    def lock_staff(self):
        return MagicMock()

    def get(self, invitation_id: str) -> Invitation | None:
        return self.rows.get(invitation_id)

    def save(self, invitation: Invitation) -> None:
        self.rows[invitation.id] = invitation

    def find_by_code_hash(self, code_hash: str) -> Invitation | None:
        return next((i for i in self.rows.values() if i.code_hash == code_hash), None)

    def list_of(self, kind: InvitationKind, company_id: str | None) -> list[Invitation]:
        return [i for i in self.rows.values() if i.kind == kind and i.company_id == company_id]

    def list_all(self) -> list[Invitation]:
        return list(self.rows.values())


class Harness:
    def __init__(self) -> None:
        self.invitations = Invitations()
        self.dao = DaoService(
            create_autospec(Database, instance=True),
            templates=create_autospec(AppClientTemplateDao, instance=True),
            instance_clients=create_autospec(AppInstanceClientDao, instance=True),
            companies=create_autospec(CompanyDao, instance=True),
            company_users=create_autospec(CompanyUserDao, instance=True),
            invitations=self.invitations,
            audit_log=create_autospec(AuditLogDao, instance=True),
            role_log=create_autospec(RoleAssignmentLogDao, instance=True))
        self.profiles = create_autospec(CompanyProfileGateway, instance=True)
        self.profiles.active_companies_with.side_effect = lambda value: [MASCHINENBAU] if value == EBWOID else []
        self.dao.companies.get.return_value = Company(MASCHINENBAU, "BPNLIUK2REMLK3F4", CompanyStatus.ACTIVE)
        self.dao.company_users.current_of.return_value = None
        self.keys = create_autospec(AttestationKeys, instance=True)
        self.keys.key.side_effect = lambda kid: JWK if kid == KID else None
        self.users = create_autospec(UserServiceImpl, instance=True)
        self.users.has_staff_role.return_value = False
        ctx = Context(Config(), create_autospec(PortalIam, instance=True), self.dao,
                      create_autospec(SubscriptionsGateway, instance=True), self.profiles)
        self.service = InvitationServiceImpl(ctx, self.users, self.keys)

    def invite(self, given: str = "Max", family: str = "Beispiel", roles: tuple[str, ...] = ("Member",),
               expires_at: dt.datetime | None = None, **fields) -> Invitation:
        invitation = Invitation(InvitationKind.COMPANY, MASCHINENBAU, given, family, list(roles),
                                InvitationCode.hash(InvitationCode.generate()),
                                expires_at or now() + dt.timedelta(days=7), ERIKA, **fields)
        self.invitations.save(invitation)
        return invitation

    def accept(self, claims: dict | None = None, **changes):
        return self.service.accept({"attestation": attestation(**changes)}, claims or MAX_CLAIMS)


@pytest.fixture
def h(monkeypatch) -> Harness:
    monkeypatch.setenv("ATTESTATION_ISSUER", ISSUER)
    monkeypatch.setenv("ATTESTATION_CLIENT_IDS", "osp-a-ui")
    monkeypatch.delenv("ATTESTATION_JWKS_FILE", raising=False)
    return Harness()


def test_a_confirmed_mandate_accepts_the_invitation_of_the_company_without_a_code(h):
    invitation = h.invite(roles=("Member", "IT Admin"))

    result = h.accept()

    assert (result.invitation_id, result.user_id, result.company_id, result.roles) == (
        invitation.id, MAX, MASCHINENBAU, ["Member", "IT Admin"])
    bound = h.users.bind.call_args
    assert bound.args[:4] == (MAX, h.dao.companies.get.return_value, ["Member", "IT Admin"], JoinedVia.INVITATION)
    assert bound.kwargs["invitation_id"] == invitation.id
    assert (bound.kwargs["given_name"], bound.kwargs["family_name"]) == ("Max", "Beispiel")
    stored = h.invitations.get(invitation.id)
    assert (stored.status, stored.accepted_by, stored.given_name) == (InvitationStatus.ACCEPTED, MAX, None)
    assert h.dao.audit_log.add.call_args.args[0].operation == "acceptInvitation"


def test_names_are_compared_as_in_the_code_path_and_the_newest_open_invitation_counts(h):
    older = h.invite(roles=("Member",), created_at=now() - dt.timedelta(days=2))
    newer = h.invite(given=" max ", family="BEISPIEL", roles=("IT Admin",))
    h.invite(given="Maria", family="Beispiel")

    assert h.accept().invitation_id == newer.id
    assert h.invitations.get(older.id).status == InvitationStatus.OPEN


def test_the_company_is_found_by_the_identifier_of_the_mandate_without_a_company_block(h):
    invitation = h.invite()

    assert h.accept(company=None).invitation_id == invitation.id   # a register mandate carries no LPID
    h.profiles.active_companies_with.assert_called_with(EBWOID)


def test_a_second_call_after_the_binding_answers_like_the_first(h):
    invitation = h.invite()
    first = h.accept()
    h.dao.company_users.current_of.return_value = CompanyUser(MAX, MASCHINENBAU, JoinedVia.INVITATION,
                                                             invitation_id=invitation.id)

    assert h.accept() == first
    assert h.users.bind.call_count == 1


@pytest.mark.parametrize(("changes", "reason"), [
    ({"typ": "JWT"}, "algorithm"),
    ({"iss": "https://other.example.org"}, "issuer"),
    ({"key": ec.generate_private_key(ec.SECP256R1())}, "signature"),
    ({"aud": "someone-else"}, "audience"),
    ({"exp": int(time.time()) - 3600}, "expired"),
    ({"iat": int(time.time()) + 3600}, "not-yet-valid"),
    ({"purpose": "onboarding"}, "claims"),          # an attestation of the registration is not a mandate to join
    ({"client_id": "another-client"}, "claims"),
    ({"person": {"given_name": "Max"}}, "claims"),
    ({"jti": None}, "claims"),
    ({"verified_at": int(time.time()) - 3600}, "too-old"),
])
def test_an_attestation_that_fails_a_check_is_refused_with_its_reason(h, changes, reason):
    h.invite()

    with pytest.raises(AttestationInvalidException) as refused:
        h.accept(**changes)

    assert refused.value.details == {"reason": reason}
    body = ExceptionTranslator.to_problem(refused.value).body()
    assert (body["status"], body["type"], body["reason"]) == (400, "urn:c2-m2:problem:attestation-invalid", reason)
    h.users.bind.assert_not_called()


@pytest.mark.parametrize("value", ["not-a-jws", "a.b.c", 7, None])
def test_an_unreadable_attestation_is_refused(h, value):
    with pytest.raises(AttestationInvalidException) as refused:
        h.service.accept({"attestation": value}, MAX_CLAIMS)
    assert refused.value.details == {"reason": "format"}


def test_without_a_configured_issuer_no_attestation_is_accepted(monkeypatch):
    monkeypatch.delenv("ATTESTATION_ISSUER", raising=False)
    h = Harness()
    h.invite()
    with pytest.raises(AttestationInvalidException) as refused:
        h.service.accept({"attestation": attestation(iss="")}, MAX_CLAIMS)
    assert refused.value.details == {"reason": "issuer"}


def test_a_mandate_that_is_not_confirmed_is_refused_with_the_reasons_of_the_connector(h):
    h.invite()
    not_confirmed = {"confirmed": False, "result": "NOT_CONFIRMED", "reasons": ["ISSUER_NOT_TRUSTED"]}

    with pytest.raises(RepresentationNotConfirmedException) as refused:
        h.accept(representation=not_confirmed, company=None, sub=None)

    body = ExceptionTranslator.to_problem(refused.value).body()
    assert (body["status"], body["type"]) == (403, "urn:c2-m2:problem:representation-not-confirmed")
    assert body["reasons"] == ["ISSUER_NOT_TRUSTED"]


def test_the_attestation_of_another_person_is_refused(h):
    h.invite()
    with pytest.raises(NameMismatchException):
        h.accept({"sub": ERIKA, "given_name": "Erika", "family_name": "Mustermann"})
    with pytest.raises(NameMismatchException):
        h.accept({"sub": ERIKA})   # names missing in the token count as a mismatch
    h.users.bind.assert_not_called()


def test_without_an_open_invitation_for_this_person_nothing_is_bound(h):
    h.invite(given="Maria")
    h.invite(status=InvitationStatus.REVOKED)
    h.invite(expires_at=now() - dt.timedelta(minutes=1))

    with pytest.raises(InvitationNotFoundException):
        h.accept()
    h.users.bind.assert_not_called()


def test_a_mandate_of_a_company_that_is_not_active_here_is_refused(h):
    h.invite()
    h.profiles.active_companies_with.side_effect = lambda value: []

    with pytest.raises(CompanyNotActiveException):
        h.accept()


def test_an_account_that_is_bound_already_stays_as_it_is(h):
    h.invite()
    h.dao.company_users.current_of.return_value = CompanyUser(MAX, "c0000002-0000-4000-8000-000000000002",
                                                             JoinedVia.ONBOARDING)
    with pytest.raises(UserAlreadyBoundException):
        h.accept()


def test_code_and_attestation_exclude_each_other(h):
    for body in ({}, {"code": "x" * 43, "attestation": attestation()}):
        with pytest.raises(ValidationException):
            h.service.accept(body, MAX_CLAIMS)


def test_keys_come_from_the_configured_file_only(tmp_path, monkeypatch):
    file = tmp_path / "jwks.json"
    file.write_text(json.dumps({"keys": [JWK]}), encoding="utf-8")
    monkeypatch.setenv("ATTESTATION_JWKS_FILE", str(file))
    keys = AttestationKeysImpl(Config())

    assert keys.key(KID) == JWK
    assert keys.key("unknown") is None


def test_the_stand_in_of_the_company_profile_finds_an_active_company_by_ebwoid_or_euid(monkeypatch):
    monkeypatch.setenv("C3_M1_URL", "")
    gateway = CompanyProfileGatewayImpl()

    assert gateway.active_companies_with(EBWOID) == [MASCHINENBAU]
    assert gateway.active_companies_with("DEXX001T.HRB100001") == [MASCHINENBAU]
    assert gateway.active_companies_with("EBWOID-DE-0000000009") == []

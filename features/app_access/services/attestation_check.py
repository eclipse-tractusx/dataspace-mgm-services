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
"""Check of a verification attestation of the EBW-Connector with the purpose `representation` (README 6.8a,
C5-M1 section 9): a person presented a mandate of a company, and the EBW-Connector attests the result.

The order of the checks is the one of 6.8a; the first failure decides the `reason` of `attestation-invalid`.
Nothing here changes state."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import jwt

from features.app_access.managers.config import Config
from features.app_access.managers.config.properties import as_int, as_list
from features.app_access.managers.ports import AttestationKeys
from features.app_access.models.exception import AttestationInvalidException, RepresentationNotConfirmedException

TYP = "ebw-attestation+jwt"
ALGORITHM = "ES256"
PURPOSE = "representation"


@dataclass(frozen=True)
class ConfirmedMandate:
    """What a valid attestation says: this person represents the company with this identifier."""
    verification_id: str
    given_name: str
    family_name: str
    company_identifiers: tuple[str, ...]   # EBWOID or EUID, as the mandate and the LPID inside it name the company


class AttestationCheck:
    def __init__(self, config: Config, keys: AttestationKeys) -> None:
        self.config = config
        self.keys = keys

    def confirmed_mandate(self, attestation: object, at: dt.datetime | None = None) -> ConfirmedMandate:
        """Raises `attestation-invalid` (400), `representation-not-confirmed` (403) or `upstream-error` (502)."""
        claims = self._signed_claims(attestation)
        self._check_validity(claims, at or dt.datetime.now(dt.UTC))
        representation, person = claims["representation"], claims["person"]
        if representation.get("confirmed") is not True:
            raise RepresentationNotConfirmedException("the EBW-Connector did not confirm the mandate",
                                                      reasons=list(representation.get("reasons") or []))
        company = claims.get("company")
        company = company if isinstance(company, dict) else {}
        identifiers = [representation.get("company_id"), company.get("ebwoid"), company.get("euid")]
        return ConfirmedMandate(str(claims["jti"]), person["given_name"], person["family_name"],
                                tuple(dict.fromkeys(str(value) for value in identifiers if value)))

    def _signed_claims(self, attestation: object) -> dict:
        """Format, type, issuer and signature: the claims of an attestation of the installation's EBW-Connector."""
        if not isinstance(attestation, str) or attestation.count(".") != 2:
            raise AttestationInvalidException("format", "attestation: a compact JWS")
        try:
            header = jwt.get_unverified_header(attestation)
            unchecked = jwt.decode(attestation, options={"verify_signature": False, "verify_aud": False,
                                                         "verify_exp": False, "verify_iat": False})
        except jwt.PyJWTError as error:
            raise AttestationInvalidException("format", f"attestation unreadable: {error}") from error
        if header.get("typ") != TYP or header.get("alg") != ALGORITHM:
            raise AttestationInvalidException("algorithm", f"typ {header.get('typ')!r}, alg {header.get('alg')!r}")
        issuer = self.config.from_properties("attestation.issuer").rstrip("/")
        if not issuer or unchecked.get("iss") != issuer:
            raise AttestationInvalidException("issuer", f"iss {unchecked.get('iss')!r}")
        key = self.keys.key(header.get("kid"))
        if key is None:
            raise AttestationInvalidException("signature", f"kid {header.get('kid')!r} is not in the JWKS")
        try:
            # Audience and times are checked afterwards, with the reasons of 6.8a.
            return jwt.decode(attestation, jwt.PyJWK(key).key, algorithms=[ALGORITHM],
                              options={"verify_aud": False, "verify_exp": False, "verify_iat": False})
        except jwt.PyJWTError as error:
            raise AttestationInvalidException("signature", str(error)) from error

    def _check_validity(self, claims: dict, at: dt.datetime) -> None:
        """Audience, times, claims, purpose, client and age (6.8a steps 4 to 7)."""
        audience = claims.get("aud")
        if self.config.from_properties("attestation.audience") not in ([audience] if isinstance(audience, str)
                                                                       else list(audience or [])):
            raise AttestationInvalidException("audience", f"aud {audience!r}")
        skew = dt.timedelta(seconds=as_int(self.config.from_properties("attestation.clock.skew.seconds")))
        expires, issued, verified = (self._moment(claims, name) for name in ("exp", "iat", "verified_at"))
        if expires <= at - skew:
            raise AttestationInvalidException("expired", "exp is in the past")
        if issued > at + skew:
            raise AttestationInvalidException("not-yet-valid", "iat is in the future")
        wrong = self._wrong_claims(claims)
        if wrong:
            raise AttestationInvalidException("claims", "missing or wrong: " + ", ".join(wrong))
        max_age = dt.timedelta(minutes=as_int(self.config.from_properties("invitation.attestation.max.age.minutes")))
        if verified < at - max_age - skew:
            raise AttestationInvalidException("too-old", "verified_at is older than the allowed age")

    def _wrong_claims(self, claims: dict) -> list[str]:
        person, representation = claims.get("person"), claims.get("representation")
        wrong = [name for name in ("jti",) if not claims.get(name)]
        if claims.get("purpose") != PURPOSE:
            wrong.append(f"purpose={PURPOSE}")
        if not isinstance(person, dict) or not (person.get("given_name") and person.get("family_name")):
            wrong.append("person")
        if not isinstance(representation, dict):
            wrong.append("representation")
        clients = as_list(self.config.from_properties("attestation.client.ids"))
        if clients and claims.get("client_id") not in clients:
            wrong.append("client_id")
        return wrong

    @staticmethod
    def _moment(claims: dict, name: str) -> dt.datetime:
        value = claims.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AttestationInvalidException("claims", f"{name} is not a numeric date")
        return dt.datetime.fromtimestamp(value, dt.UTC)

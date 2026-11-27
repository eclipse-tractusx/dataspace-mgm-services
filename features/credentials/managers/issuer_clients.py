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
#  Assisted-By: Claude Code (claude-sonnet-5-5)
#################################################################################
"""Clients of the issuers of the credentials (README 11.3 to 11.5): one class per route of README 6.3.

A route object has `name`, `prepare(ctx)` (once per run, before the first order),
`order(ctx, credential_type, attempt)` (returns `(request_ref, issuer_did)`), `cancel(row)` and `revoke(row)`
(True = revoked, False = the route cannot revoke). Which route is used is a business rule
(`services/issuer_routes.py`); the built-in stand-in `STUB` is `services/stub_issuer.py`.

Configuration is read from the environment at call time (AGENTS.md rule 6).
"""
from __future__ import annotations

import time
from typing import Protocol

import httpx

from features.credentials.managers import config, neighbour_client
from features.credentials.models.errors import MODULE, issuer_rejected, wallet_not_ready
from features.credentials.models.errors import upstream as _upstream
from features.credentials.models.values import CREDENTIAL_ISSUER, CSP_ISSUER, ISSUER_SERVICE
from portal_common import csp, http, settings, spec


# ------------------------------------------------------------------------------------- helpers
def _callback_url(kind: str) -> str:
    """`{CALLBACK_BASE_URL}{base path}/issuer-callbacks/{kind}` (base path `/api/credentials`, ADR-0003); without
    the variable the address of the installation (OPEN-QUESTIONS.md)."""
    return f"{config.callback_base_url()}{spec.module(MODULE).base_path}/issuer-callbacks/{kind}"


def _member_of() -> str | None:
    return (settings.get("dataspace") or {}).get("memberOf")


def _holder_access(ctx: dict) -> dict:
    """Holder access from C4-M2, once per run just before the first order; kept in memory only."""
    if "access" not in ctx:
        access = neighbour_client.holder_access(ctx["company"]["id"])
        if not access:
            raise wallet_not_ready("no holder access for the wallet")
        ctx["access"] = access
    return ctx["access"]


def _identity_request(ctx: dict, credential_type: str, attempt: int, issuer_did: str, identifier: str) -> str:
    """Credential request in the identity interface of the holder's wallet (README 11.4); returns `holderPid`."""
    access = _holder_access(ctx)
    holder_pid = f"{ctx['company']['id']}:{credential_type}:{attempt}"
    credential = {"type": identifier, "format": config.credential_format()}
    try:
        r = http.request("POST", f"{access['identityApiUrl'].rstrip('/')}/participants/{access['participantContextId']}"
                         "/credentials/request",
                         json={"issuerDid": issuer_did, "holderPid": holder_pid, "credentials": [credential]},
                         headers={"x-api-key": access["apiKey"]})
    except httpx.HTTPError as e:
        raise _upstream(f"wallet identity API: {type(e).__name__}") from e
    if not r.is_success:
        raise _upstream(f"wallet identity API answered {r.status_code}")
    return holder_pid


# ------------------------------------------------------------------------------------- CSP_ISSUER
class IssuerRoute(Protocol):
    """What a route of README 6.3 does; the services only talk to this."""

    name: str

    def prepare(self, ctx: dict) -> None: ...

    def order(self, ctx: dict, credential_type: str, attempt: int) -> tuple[str, str | None]: ...

    def cancel(self, row: dict) -> None: ...

    def revoke(self, row: dict) -> bool: ...


class CspIssuerRoute:
    """CSP issuer (README 11.5): holder and grant at the CSP, request in the holder's wallet."""

    name: str = CSP_ISSUER

    @staticmethod
    def _csp(method: str, path: str, body: dict | None = None, revocation: bool = False) -> None:
        try:
            status, _ = csp.request(config.csp_issuer_url(), method, path, body)
        except csp.CspUnavailable as e:
            raise _upstream(f"CSP issuer: {e}") from e
        if 200 <= status < 300:
            return
        if not revocation and status in (403, 404, 409, 422):
            raise issuer_rejected(f"CSP issuer answered {status}")
        raise _upstream(f"CSP issuer answered {status}")

    def prepare(self, ctx: dict) -> None:
        _holder_access(ctx)                       # once per run, never sent to the CSP
        self._csp("PUT", f"/holders/{ctx['company']['bpn'].upper()}", {"did": ctx["wallet"]["did"]})

    def order(self, ctx: dict, credential_type: str, attempt: int) -> tuple[str, str | None]:
        bpn, kind = ctx["company"]["bpn"].upper(), credential_type.lower()
        grant: dict[str, str | None] = {"callbackUrl": _callback_url(kind)}
        if kind == "membership":
            grant["memberOf"] = _member_of()
        self._csp("PUT", f"/holders/{bpn}/grants/{kind}", grant)
        issuer_did = config.csp_issuer_did()
        identifier = config.csp_issuer_definitions()[credential_type]
        return _identity_request(ctx, credential_type, attempt, issuer_did, identifier), issuer_did

    def _remove_grant(self, row: dict) -> None:
        self._csp("DELETE", f"/holders/{row['bpn']}/grants/{row['credential_type'].lower()}", revocation=True)

    def cancel(self, row: dict) -> None:
        """README 8.2: the grant is removed first, so that a request still running is no longer issued."""
        self._remove_grant(row)

    def revoke(self, row: dict) -> bool:
        self._remove_grant(row)                   # 204: removes the grant and revokes issued credentials
        return True


# ---------------------------------------------------------------------------------- CREDENTIAL_ISSUER
_issuer_tokens: dict[str, tuple[str, float]] = {}


class CredentialIssuerRoute:
    """Own Credential Issuer (README 11.3): the issuer writes into the wallet; revocation is not supported in 0.2."""

    name: str = CREDENTIAL_ISSUER

    @staticmethod
    def _token() -> str:
        url, form = config.credential_issuer_token_request()
        cached = _issuer_tokens.get(url)
        if cached and cached[1] > time.time() + 30:
            return cached[0]
        try:
            r = http.request("POST", url, data=form)
            body = r.json() if r.status_code == 200 else {}
        except (httpx.HTTPError, ValueError) as e:
            raise _upstream(f"Credential Issuer token endpoint: {type(e).__name__}") from e
        if "access_token" not in body:
            raise _upstream(f"Credential Issuer token endpoint answered {r.status_code}")
        _issuer_tokens[url] = (body["access_token"], time.time() + int(body.get("expires_in", 300)))
        return body["access_token"]

    def prepare(self, ctx: dict) -> None:
        _holder_access(ctx)

    def order(self, ctx: dict, credential_type: str, attempt: int) -> tuple[str, str | None]:
        access, kind = _holder_access(ctx), credential_type.lower()
        body = {"holder": access["holder"], "businessPartnerNumber": ctx["company"]["bpn"].upper(),
                "technicalUserDetails": {"walletUrl": access["walletUrl"], "clientId": access["clientId"],
                                         "clientSecret": access["clientSecret"]},
                "callbackUrl": _callback_url(kind)}
        if kind == "membership":
            body["memberOf"] = _member_of()
        try:
            r = http.request("POST", config.credential_issuer_url() + f"/api/issuer/{kind}",
                             json=body, headers={"Authorization": "Bearer " + self._token()})
        except httpx.HTTPError as e:
            raise _upstream(f"Credential Issuer: {type(e).__name__}") from e
        if not r.is_success:                      # every 2xx counts as accepted
            raise _upstream(f"Credential Issuer answered {r.status_code}")
        return "", None

    def cancel(self, row: dict) -> None:
        """Nothing to remove at the Credential Issuer."""

    def revoke(self, row: dict) -> bool:
        return False                              # README 6.3: not supported -> REVOCATION_PENDING


# ------------------------------------------------------------------------------------ ISSUER_SERVICE
class IssuerServiceRoute:
    """Own IssuerService (README 11.4). The paths of the administration interface are provisional (the spec says
    to check them against the version in use, OPEN-QUESTIONS.md)."""

    name: str = ISSUER_SERVICE

    @staticmethod
    def _admin(method: str, path: str, body: dict | None = None, accept: tuple[int, ...] = ()) -> None:
        try:
            r = http.request(method, config.issuer_service_admin_url() + path, json=body,
                             headers={"x-api-key": config.issuer_service_api_key()})
        except httpx.HTTPError as e:
            raise _upstream(f"IssuerService: {type(e).__name__}") from e
        if not (r.is_success or r.status_code in accept):
            raise _upstream(f"IssuerService answered {r.status_code}")

    def prepare(self, ctx: dict) -> None:
        _holder_access(ctx)
        company = ctx["company"]
        self._admin("POST", "/holders", {"holderId": company["bpn"].upper(), "did": ctx["wallet"]["did"],
                                         "name": company.get("name"), "properties": {"memberOf": _member_of()}},
                    accept=(409,))                # an existing holder counts as success

    def order(self, ctx: dict, credential_type: str, attempt: int) -> tuple[str, str | None]:
        issuer_did = config.issuer_did()
        identifier = config.issuer_service_definitions()[credential_type]
        return _identity_request(ctx, credential_type, attempt, issuer_did, identifier), issuer_did

    def cancel(self, row: dict) -> None:
        """Nothing to remove."""

    def revoke(self, row: dict) -> bool:
        ident = config.issuer_service_definitions()[row["credential_type"]]
        self._admin("POST", f"/holders/{row['bpn']}/credentials/revoke", {"credentialDefinition": ident})
        return True


# route name -> client class (the route `STUB` is the stand-in of services/stub_issuer.py)
CLIENTS: dict[str, type[IssuerRoute]] = {
    CSP_ISSUER: CspIssuerRoute, CREDENTIAL_ISSUER: CredentialIssuerRoute, ISSUER_SERVICE: IssuerServiceRoute}

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
"""Issuer routes of the credentials (README 6.3): which route triggers a credential at an issuer.

`select_route(wallet)` applies the rules of README 6.3 and returns the route name; `get(name)` returns the route
object. A route object has `name`, `prepare(ctx)` (once per run, before the first order),
`order(ctx, credential_type, attempt)` (returns `(request_ref, issuer_did)`), `cancel(row)` and `revoke(row)`
(True = revoked, False = the route cannot revoke). The clients of the real issuers are managers
(`managers/issuer_clients.py`); the built-in stand-in is `stub_issuer.py`.
"""
from __future__ import annotations

from features.credentials.managers import config
from features.credentials.managers.issuer_clients import CLIENTS, IssuerRoute
from features.credentials.models.errors import no_route
from features.credentials.models.values import CSP_ISSUER, FITS, STUB
from features.credentials.services.stub_issuer import StubRoute


def select_route(wallet: dict) -> str:
    """README 6.3, in this order. An own wallet (`BRING_YOUR_OWN`, `CREDENTIAL_OFFER`) has no route in
    version 0.2; it is rejected before rule 2 (OPEN-QUESTIONS.md, case 5 against rule 2)."""
    provider, mode = wallet.get("provider"), wallet.get("issuanceMode")
    if provider == "STUB":                                                   # rule 1
        return STUB
    if provider == "BRING_YOUR_OWN" or mode == "CREDENTIAL_OFFER":
        raise no_route("an own wallet has no issuer route in version 0.2")
    if config.issuer_mode() == "CSP":                                        # rule 3
        if not config.csp_issuer_configured():
            return STUB
        if mode != "HOLDER_REQUESTS":
            raise no_route("the CSP issuer issues only into wallets with issuance mode HOLDER_REQUESTS")
        return CSP_ISSUER
    routes = config.issuer_routes()                                          # rule 2
    if not config.issuer_routes_configured():
        return STUB
    route = routes.get(provider or "")
    if route is None:
        raise no_route(f"no entry in ISSUER_ROUTES for the wallet provider {provider}")
    if FITS.get(route) != mode:                                              # rule 4
        raise no_route(f"route {route} does not fit the issuance mode {mode}")
    return route


_stub = StubRoute()


def stub_orders() -> list[dict]:
    """Every order the STUB route received (tests)."""
    return list(_stub.orders)


def flush_stub() -> None:
    """Fires every pending STUB issuer timer now (tests)."""
    _stub.flush()


def get(name: str) -> IssuerRoute:
    if name == STUB:
        return _stub
    if name not in CLIENTS:
        raise no_route(f"route {name} is not available")
    return CLIENTS[name]()


def reset() -> None:
    _stub.reset()

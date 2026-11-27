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
"""Provider adapters of C4-M2: the registry, the choice of the provider (README 6.1) and the stand-in helpers.

The adapters (README 6.11) are in `sap_div.py`, `identity_hub.py` and `csp.py` of this package; the SAP DIV
callback routes are the controllers `callbacks/sap_div/`. Everything the services and the tests need is reached
through this package: `get`, `enabled`, `default_provider`, `on_callback`, `stand_in_documents`, `orders`,
`flush_stand_in` and `reset`. Environment variables are read at call time.
"""
from __future__ import annotations

import os
from collections.abc import Callable

from . import common
from . import csp as providers_csp
from . import identity_hub as providers_identity_hub
from . import sap_div as providers_sap_div

PROVIDERS = ("SAP_DIV", "IDENTITY_HUB", "CSP")
_ADAPTERS: dict[str, common.ProviderAdapter] = {
    "SAP_DIV": providers_sap_div.SapDivAdapter(),
    "IDENTITY_HUB": providers_identity_hub.IdentityHubAdapter(),
    "CSP": providers_csp.CspAdapter(),
}


def get(provider: str) -> common.ProviderAdapter:
    """The adapter of `SAP_DIV`, `IDENTITY_HUB` or `CSP`."""
    try:
        return _ADAPTERS[provider]
    except KeyError:
        raise ValueError(f"no adapter for provider {provider!r}") from None


def enabled() -> list[str]:
    """README 4 `ENABLED_PROVIDERS`: comma-separated, empty = `SAP_DIV,IDENTITY_HUB,CSP`."""
    names = [name.strip().upper() for name in os.environ.get("ENABLED_PROVIDERS", "").split(",") if name.strip()]
    chosen = [name for name in dict.fromkeys(names) if name in PROVIDERS]
    return chosen or list(PROVIDERS)


def default_provider() -> str:
    """README 4 `DEFAULT_PROVIDER`: empty = `CSP`."""
    return os.environ.get("DEFAULT_PROVIDER", "").strip().upper() or "CSP"


def on_callback(name: str, handler: Callable[..., None]) -> None:
    """Register the service function a built-in stand-in calls back (README 7.6): `wallet-created`,
    `account-created` or `account-deleted`. The services register themselves when they are imported, so the
    adapters never import the layer above them."""
    common.on_callback(name, handler)


def stand_in_documents() -> dict[str, dict]:
    """DID -> DID document of every built-in stand-in wallet, for the built-in resolution (README 11.4)."""
    return common.documents()


def orders() -> list[dict]:
    """Every order a built-in stand-in received: `{provider, bpn, kind}` plus `external_id` for accounts."""
    return common.orders()


def flush_stand_in() -> None:
    """Run every pending stand-in callback now (tests do not wait for `STUB_CALLBACK_DELAY_SECONDS`)."""
    common.flush()


def reset() -> None:
    """Forget orders, documents, pending callbacks and the state of the built-in stand-ins."""
    common.reset()
    providers_sap_div.reset()
    providers_identity_hub.reset()
    providers_csp.reset()

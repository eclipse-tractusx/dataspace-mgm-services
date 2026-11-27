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
"""Calls to the provider's `setupUrl` and `callbackUrl` with a token of its `tokenUrl` (client credentials, 11.2)."""
from __future__ import annotations

from typing import Literal

import httpx

from features.subscriptions.managers import provider_configuration_repository
from features.subscriptions.models.errors import problem
from portal_common import http


def call(provider_company_id: str, kind: Literal["setup", "callback"], body: dict) -> None:
    """POST `body` to the setup or callback URL of the provider's configuration."""
    cfg = provider_configuration_repository.get(provider_company_id)
    if not cfg:
        raise problem(409, "invalid-state", detail="provider has no configuration", retryable=False)
    url = cfg.setup_url if kind == "setup" else cfg.callback_url
    try:
        t = http.request("POST", cfg.token_url, data={"grant_type": "client_credentials", "client_id": cfg.client_id,
                                                      "client_secret": cfg.client_secret})
        if t.status_code != 200:
            raise problem(502, "provider-rejected", detail=f"token {t.status_code}",
                          retryable=t.status_code >= 500)
        r = http.request("POST", url, json=body, headers={"Authorization": "Bearer " + t.json()["access_token"]})
    except httpx.HTTPError as e:
        raise problem(502, "upstream-error", detail=type(e).__name__, retryable=True) from e
    if not r.is_success:
        raise problem(502, "provider-rejected" if r.status_code < 500 else "upstream-error",
                      detail=f"{kind} {r.status_code}", retryable=r.status_code >= 500)

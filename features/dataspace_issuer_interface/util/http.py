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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""HTTP request utility shared by the issuer and wallet callers."""

from __future__ import annotations

import httpx

from portal_common import http as portal_http

from ..exceptions.issuer_caller_error import IssuerCallerError


def _request(
    target: str,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: dict[str, object] | None = None,
    accepted: tuple[int, ...] = (),
) -> httpx.Response:
    """Send one request using local state so callers can safely run concurrently."""
    request_options: dict[str, object] = {"headers": headers}
    if body is not None:
        request_options["json"] = body
    try:
        response = portal_http.request(method, url, **request_options)
    except httpx.HTTPError as error:
        raise IssuerCallerError(f"{target} not reachable: {type(error).__name__}", retryable=True) from error

    if response.status_code in accepted or 200 <= response.status_code < 300:
        return response
    retryable = response.status_code == 408 or response.status_code == 429 or response.status_code >= 500
    raise IssuerCallerError(f"{target} answered {response.status_code}", retryable=retryable)

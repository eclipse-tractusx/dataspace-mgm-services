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
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from features.app_access.managers.config import Config
from features.app_access.managers.config.properties import as_int
from features.app_access.managers.ports import AttestationKeys
from features.app_access.models.exception import UpstreamErrorException
from portal_common import http

RELOAD_PAUSE_SECONDS = 60


class AttestationKeysImpl(AttestationKeys):
    """JWKS of the EBW-Connector: `ATTESTATION_JWKS_FILE` (tests, no fetch) or `ATTESTATION_JWKS_URL`, by default
    `{ATTESTATION_ISSUER}/jwks`, with a cache and at most one reload per minute for an unknown `kid` (11.4).
    Header parameters of an attestation such as `jku` or `jwk` never name a key."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._keys: list[dict] = []
        self._fetched_at = 0.0
        self._reloaded_at = 0.0

    def key(self, kid: str | None) -> dict | None:
        file = self.config.from_properties("attestation.jwks.file")
        if file:
            return self._find(self._read(Path(file)), kid)
        found = self._find(self._cached(), kid)
        if found is None and time.monotonic() - self._reloaded_at > RELOAD_PAUSE_SECONDS:
            self._reloaded_at = time.monotonic()
            self._keys = []
            found = self._find(self._cached(), kid)
        return found

    @staticmethod
    def _find(keys: list[dict], kid: str | None) -> dict | None:
        return next((key for key in keys if key.get("kid") == kid), None)

    @staticmethod
    def _read(file: Path) -> list[dict]:
        try:
            return json.loads(file.read_text(encoding="utf-8")).get("keys") or []
        except (OSError, ValueError) as error:
            raise UpstreamErrorException(f"JWKS file unreadable: {error}", retryable=True) from error

    def _cached(self) -> list[dict]:
        age = time.monotonic() - self._fetched_at
        if self._keys and age < as_int(self.config.from_properties("attestation.jwks.cache.seconds")):
            return self._keys
        issuer = self.config.from_properties("attestation.issuer").rstrip("/")
        url = self.config.from_properties("attestation.jwks.url") or f"{issuer}/jwks"
        try:
            # portal_common.http also reaches an EBW-Connector stand-in registered in-process ({BASE_URL}/ebw)
            response = http.request("GET", url, timeout=5.0)
            response.raise_for_status()
            self._keys = response.json().get("keys") or []
        except (httpx.HTTPError, ValueError) as error:
            raise UpstreamErrorException(f"JWKS of the EBW-Connector not reachable: {error}", retryable=True) from error
        self._fetched_at = time.monotonic()
        return self._keys

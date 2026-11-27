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
"""Call-time configuration for the optional IssuerService caller."""

from __future__ import annotations

import os


class IssuerServiceConfiguration:
    """Reads environment configuration when an operation is called."""

    def get_env(self, variable: str, default: str = "") -> str:
        """Read one environment variable, optionally using a default value."""
        return os.environ.get(variable, default)

    def admin_participant_url(self) -> str:
        """Return the IssuerService participant-admin base URL."""
        base_url = self.get_env("ISSUER_SERVICE_ADMIN_URL").strip().rstrip("/")
        if "/participants/" in base_url:
            return base_url
        participant_id = self.get_env("ISSUER_SERVICE_PARTICIPANT_ID", "issuer").strip()
        api_version = self.get_env("ISSUER_SERVICE_API_VERSION", "v1beta").strip().strip("/") or "v1beta"
        if base_url.endswith("/api/admin"):
            return f"{base_url}/{api_version}/participants/{participant_id}"
        return f"{base_url}/api/admin/{api_version}/participants/{participant_id}"

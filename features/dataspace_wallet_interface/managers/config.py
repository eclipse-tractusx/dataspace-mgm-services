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
"""Configuration of the dataspace wallets that the services read (README 4), always at call time (AGENTS.md rule 6).

The provider adapters, the encryption and the DID resolution read their own variables in their managers.
"""
from __future__ import annotations

import os

DEFAULT_CALLBACK_CLIENT = "sa-div-callback"


def text(name: str) -> str:
    """A variable without surrounding blanks; empty when unset."""
    return os.environ.get(name, "").strip()


def positive(name: str, default: float) -> float:
    """A positive number; the default for unset or unusable values."""
    try:
        value = float(text(name))
    except ValueError:
        return default
    return value if value > 0 else default


def did_validation_max_hours() -> float:
    return positive("DID_VALIDATION_MAX_HOURS", 168)


def did_validation_interval_minutes() -> float:
    return positive("DID_VALIDATION_INTERVAL_MINUTES", 10)


def provider_callback_timeout_minutes() -> float:
    return positive("PROVIDER_CALLBACK_TIMEOUT_MINUTES", 1440)


def timer_interval_seconds() -> float:
    return positive("TIMER_INTERVAL_SECONDS", 60)


def account_credentials_retention_days() -> float:
    return positive("ACCOUNT_CREDENTIALS_RETENTION_DAYS", 30)


def sap_div_did_document_base_url() -> str:
    return text("SAP_DIV_DID_DOCUMENT_BASE_URL").rstrip("/")


def sap_div_callback_client_id() -> str:
    return text("SAP_DIV_CALLBACK_CLIENT_ID") or DEFAULT_CALLBACK_CLIENT


def bdrs_public_url() -> str | None:
    return text("BDRS_PUBLIC_URL") or None


def identityhub_sts_token_url() -> str | None:
    return text("IDENTITYHUB_STS_TOKEN_URL") or None

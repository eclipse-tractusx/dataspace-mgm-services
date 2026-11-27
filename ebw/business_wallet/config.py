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
"""Settings of the Business Wallet."""

import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from common.jose import load_or_create_key, self_signed_cert

HERE = Path(__file__).parent

PUBLIC_URL = (os.environ.get("PUBLIC_URL") or "http://localhost:8078").rstrip("/")
HOST = urlsplit(PUBLIC_URL).hostname
SECURE = PUBLIC_URL.startswith("https")
CONNECTOR_URL = (os.environ.get("CONNECTOR_URL") or "http://localhost:8077").rstrip("/")
CLIENT_ID = os.environ.get("CLIENT_ID") or "business-wallet"
KEY_DIR = Path(os.environ.get("KEY_DIR") or HERE / ".keys")
DATA_DIR = Path(os.environ.get("DATA_DIR") or HERE / "data")
# Status lists are read by the EBW-Connector only, so a local address survives a new tunnel address.
STATUS_BASE_URL = (os.environ.get("STATUS_BASE_URL") or PUBLIC_URL).rstrip("/")

# One key: holder key of the LPID, issuer key of the mandates, client key at the EBW-Connector (C5-M1 11.2).
WALLET_KEY = load_or_create_key(KEY_DIR / "wallet.pem")
WALLET_CERT = self_signed_cert(WALLET_KEY, HOST, "Business Wallet")
WALLET_ADDRESS = f"{PUBLIC_URL}/present"

_session_key = KEY_DIR / "session.key"
if not _session_key.exists():
    _session_key.write_bytes(secrets.token_bytes(32))
SESSION_SECRET = _session_key.read_bytes()

LPID_VCT = os.environ.get("LPID_VCT") or "urn:tx:test:lpid:1"
MANDATE_VCT = os.environ.get("MANDATE_VCT") or "urn:tx:test:mandate:1"
MANDATE_VALIDITY_SECONDS = 365 * 24 * 3600
# The LPID inside a mandate (C5-M1 6.5 rule 4, 11.2): name of the claim and the LPID claims disclosed in it.
COMPANY_CREDENTIAL_CLAIM = "company_credential"
COMPANY_CREDENTIAL_DISCLOSED = ["legal_name", "ebwoid", "euid", "country"]

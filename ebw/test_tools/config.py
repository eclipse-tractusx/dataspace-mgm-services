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
"""Settings of the test tools: test issuer, trust list of the core services, demo OSP."""

import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from common.jose import load_or_create_key, self_signed_cert, signing_jwk

HERE = Path(__file__).parent

PUBLIC_URL = (os.environ.get("PUBLIC_URL") or "http://localhost:8079").rstrip("/")
HOST = urlsplit(PUBLIC_URL).hostname
CONNECTOR_URL = (os.environ.get("CONNECTOR_URL") or "http://localhost:8077").rstrip("/")
# Address of the Business Wallet of the stack, for the button that opens the LPID offer there
BUSINESS_WALLET_URL = (os.environ.get("BUSINESS_WALLET_URL") or "http://localhost:8078").rstrip("/")
KEY_DIR = Path(os.environ.get("KEY_DIR") or HERE / ".keys")
DATA_DIR = Path(os.environ.get("DATA_DIR") or HERE / "data")

ISSUER_KEY = load_or_create_key(KEY_DIR / "issuer.pem")
ISSUER_CERT = self_signed_cert(ISSUER_KEY, HOST, "EBW test issuer")
TRUST_LIST_KEY = load_or_create_key(KEY_DIR / "trust-list.pem")
OSP_KEY = load_or_create_key(KEY_DIR / "osp-client.pem")
OSP_CLIENT_ID = "demo-osp"

# Public key of the trust list for the EBW-Connector (TRUST_LIST_SIGNER_FILE).
(KEY_DIR / "trust-list-signer.json").write_text(json.dumps({"keys": [signing_jwk(TRUST_LIST_KEY)]}, indent=1))

_session_key = KEY_DIR / "session.key"
if not _session_key.exists():
    _session_key.write_bytes(secrets.token_bytes(32))
SESSION_SECRET = _session_key.read_bytes()

CREDENTIAL_VALIDITY_SECONDS = 365 * 24 * 3600

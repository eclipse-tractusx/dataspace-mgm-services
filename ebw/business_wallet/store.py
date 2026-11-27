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
"""State of the Business Wallet in a JSON file: held credentials and issued mandates."""

import json
import time

from common import sdjwt
from business_wallet import config

PATH = config.DATA_DIR / "wallet.json"


def load() -> dict:
    return json.loads(PATH.read_text()) if PATH.exists() else {"credentials": [], "mandates": []}


def save(state: dict) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(state, indent=1, ensure_ascii=False))


def credentials() -> list[str]:
    return load()["credentials"]


def add_credential(credential: str) -> None:
    state = load()
    state["credentials"].append(credential)
    save(state)


def lpid_credential() -> str | None:
    """The most recent LPID as received, or None."""
    for credential in reversed(credentials()):
        if sdjwt.payload_of(credential).get("vct") == config.LPID_VCT:
            return credential
    return None


def lpid() -> dict | None:
    """Claims of the most recent LPID, or None."""
    credential = lpid_credential()
    if credential is None:
        return None
    _, disclosures, _ = sdjwt.split(credential)
    return sdjwt.resolve(sdjwt.payload_of(credential), disclosures)


def mandates() -> list[dict]:
    return load()["mandates"]


def add_mandate(mandate: dict) -> None:
    state = load()
    state["mandates"].append({**mandate, "state": "OFFERED", "created_at": time.strftime("%Y-%m-%d %H:%M")})
    save(state)


def update_mandate(mandate_id: str, **changes) -> dict | None:
    state = load()
    for mandate in state["mandates"]:
        if mandate["id"] == mandate_id:
            mandate.update(changes)
            save(state)
            return mandate
    return None

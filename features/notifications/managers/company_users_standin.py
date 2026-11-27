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
"""Built-in stand-in of C2-M2 for the recipients (README 11.2): `data/stub-company-users.json`, the data of
README 14, used when the address of c2-m2 is empty."""
from __future__ import annotations

import json
from pathlib import Path

STUB_COMPANY_USERS = Path(__file__).parent / "data" / "stub-company-users.json"   # README 11.2, 14
_stub_cache: tuple[int, dict] | None = None   # (file version, parsed table); replaced whole, so no lock


def company_users(company_id: str, portal_role: str) -> list[str]:
    """`companyId` -> portal role -> `sub` values of the stand-in file."""
    return list(_stub_table().get(company_id, {}).get(portal_role, []))


def _stub_table() -> dict:
    """The stand-in file, parsed once and again only when it changes on disk."""
    global _stub_cache
    version = STUB_COMPANY_USERS.stat().st_mtime_ns
    cached = _stub_cache
    if cached is None or cached[0] != version:
        cached = _stub_cache = (version, json.loads(STUB_COMPANY_USERS.read_text(encoding="utf-8")))
    return cached[1]

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
"""Test environment: installation OSP A at http://osp-a.test, everything in one process."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = "http://osp-a.test"
os.environ.setdefault("SPEC_DIR", str(ROOT / "spec"))
os.environ["SETTINGS_FILE"] = str(ROOT / "config" / "osp-a" / "installation.json")
os.environ["BASE_URL"] = BASE
os.environ.pop("IAM_URL", None)
os.environ.pop("MODULE_URLS", None)
os.environ["MODULE_URLS_DEFAULT"] = "in-process"

from portal_common import events, http, settings, tokens  # noqa: E402
from tools import test_iam  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_state():
    settings.reset()
    tokens.reset()
    test_iam.reset()
    events.RELAY.reset()
    yield
    http._local.clear()


def team_modules_needing_keycloak() -> list[str]:
    """C2-M2 and C2-M3 of a team call the Admin API of the Portal IAM; the in-memory test IAM has none."""
    from scaffold import registry
    return [e.id for e in registry.load() if e.id in ("c2-m2", "c2-m3") and e.kind in ("team", "feature")]


needs_admin_api = pytest.mark.skipif(
    bool(team_modules_needing_keycloak()),
    reason="C2-M2/C2-M3 of a team need Keycloak: docker compose up -d, then uv run python demo.py")


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def person_token(key: str) -> str:
    iam = test_iam.iam()
    return iam.person_token(iam.find(key))

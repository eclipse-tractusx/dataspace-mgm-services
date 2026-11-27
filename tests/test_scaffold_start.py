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
"""Start of an installation: fresh state with the test tools, kept data in operation (`RESET_ON_START`),
and `POST /scaffold/reset` only as a test tool."""
import pytest

from portal_common import events
from scaffold import app as scaffold_app

MARK = {"type": "KeptOverTheStart", "source": "urn:test"}


def _start_with_state(monkeypatch, **env) -> tuple[set[str], bool]:
    """Starts the installation over existing state; returns its paths and whether the state is still there."""
    monkeypatch.delenv("RESET_ON_START", raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    events.RELAY.log.append(MARK)
    app = scaffold_app.create_app()
    return set(app.openapi()["paths"]), MARK in events.RELAY.log


def test_with_the_test_tools_every_start_begins_with_fresh_state(monkeypatch):
    paths, kept = _start_with_state(monkeypatch)
    assert not kept
    assert "/scaffold/reset" in paths


def test_an_operated_installation_keeps_its_data_over_a_restart(monkeypatch):
    paths, kept = _start_with_state(monkeypatch, TEST_TOOLS="false", IAM_URL="http://iam.test/auth")
    assert kept
    assert "/scaffold/reset" not in paths   # it would empty the installation without a sign-in


@pytest.mark.parametrize("env, kept", [
    ({"RESET_ON_START": "false"}, True),   # with the test tools, data kept
    ({"RESET_ON_START": "true", "TEST_TOOLS": "false", "IAM_URL": "http://iam.test/auth"}, False),   # operation, fresh
])
def test_reset_on_start_overrides_the_default(monkeypatch, env, kept):
    assert _start_with_state(monkeypatch, **env)[1] is kept

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
#  Assisted-By: Antigravity (Gemini 3.8 Flash)
#################################################################################
"""Tests for startup database persistence across features (Issue #101).

Starting the application (scaffold create_app, runtimes create_runtime) creates tables
that do not exist yet but keeps existing data in persistent database tables.
Explicit resets (/scaffold/reset, reset_all) continue to drop and recreate tables for tests.
"""
import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features import notifications as n
from portal_common import database
from runtimes import create_runtime


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    saved_env = dict(os.environ)
    database.dispose()
    yield
    database.dispose()
    os.environ.clear()
    os.environ.update(saved_env)


def test_startup_keeps_database_data_on_restart(tmp_path: Path, monkeypatch):
    """Building the application retains existing records in feature database tables."""
    db_file = tmp_path / "notif_persist.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("NOTIFICATIONS_DATABASE_URL", db_url)

    # Start 1: Run feature runtime and process an event
    app1 = create_runtime(n)
    with TestClient(app1):
        n.on_event({
            "specversion": "1.0",
            "id": "e-1",
            "source": "urn:c1-m2",
            "type": "ApplicationSubmitted",
            "time": "2026-11-20T09:00:00Z",
            "data": {
                "applicationId": "11111111-1111-1111-1111-111111111111",
                "companyId": "22222222-2222-2222-2222-222222222222",
                "applicantSub": "33333333-3333-3333-3333-333333333333",
            },
        })

    database.dispose()
    with sqlite3.connect(db_file) as conn:
        count1 = conn.execute("select count(*) from notification").fetchone()[0]
    assert count1 == 2, f"Expected 2 notifications created, got {count1}"

    # Start 2: Rebuilding the app as during a pod restart / rolling update must NOT wipe tables
    app2 = create_runtime(n)
    assert app2 is not None

    database.dispose()
    with sqlite3.connect(db_file) as conn:
        count2 = conn.execute("select count(*) from notification").fetchone()[0]
    assert count2 == count1, f"Expected records preserved across restart, but count changed to {count2}"


def test_scaffold_reset_still_empties_database(tmp_path: Path, monkeypatch):
    """Calling /scaffold/reset explicitly drops and recreates tables for test isolation."""
    db_file = tmp_path / "notif_reset.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    monkeypatch.setenv("NOTIFICATIONS_DATABASE_URL", db_url)

    app_inst = create_runtime(n)
    client = TestClient(app_inst)
    with client:
        n.on_event({
            "specversion": "1.0",
            "id": "e-2",
            "source": "urn:c1-m2",
            "type": "ApplicationSubmitted",
            "time": "2026-11-20T09:00:00Z",
            "data": {
                "applicationId": "11111111-1111-1111-1111-111111111111",
                "companyId": "22222222-2222-2222-2222-222222222222",
                "applicantSub": "33333333-3333-3333-3333-333333333333",
            },
        })

    with sqlite3.connect(db_file) as conn:
        before = conn.execute("select count(*) from notification").fetchone()[0]
    assert before > 0

    # Explicit scaffold reset
    response = client.post("/scaffold/reset")
    assert response.status_code == 200
    assert response.json() == {"reset": True}

    database.dispose()
    with sqlite3.connect(db_file) as conn:
        after = conn.execute("select count(*) from notification").fetchone()[0]
    assert after == 0, f"Expected table to be emptied on explicit reset, got {after}"

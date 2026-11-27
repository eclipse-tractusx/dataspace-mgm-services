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
"""Tests for database isolation in multi-feature runtimes (ADR-0003, FRAMEWORK 4.9, Closes #102).

A runtime serving more than one feature refuses to start when DATABASE_URL is set without
dedicated database variables (<FEATURE>_DATABASE_URL, <SPEC_ID>_DATABASE_URL) for each feature.
"""
import os

import pytest

from portal_common import database
from runtimes import operations
from scaffold import app

CLEAN_ENV = (
    "DATABASE_URL",
    "NOTIFICATIONS_DATABASE_URL",
    "C11_M1_DATABASE_URL",
    "PROCESS_ORCHESTRATION_DATABASE_URL",
    "C12_M1_DATABASE_URL",
    "REGISTRATION_DATABASE_URL",
    "C1_M2_DATABASE_URL",
    "COMPANY_PROFILE_DATABASE_URL",
    "C3_M1_DATABASE_URL",
    "APPLICATION_REVIEW_DATABASE_URL",
    "C1_M3_DATABASE_URL",
)


@pytest.fixture(autouse=True)
def _clean_database_env(monkeypatch):
    """Clean database environment variables and restore full process environment afterwards.

    A split runtime sets `<MODULE>_URL=in-process` for its features; keep that out of other tests.
    """
    saved_env = dict(os.environ)
    for var in CLEAN_ENV:
        monkeypatch.delenv(var, raising=False)
    database.dispose()
    yield
    database.dispose()
    os.environ.clear()
    os.environ.update(saved_env)


def test_multi_feature_runtime_refuses_shared_database_url(monkeypatch):
    """A runtime with multiple features refuses to start when DATABASE_URL is set without feature URLs."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/shared.db")

    with pytest.raises(ValueError) as exc_info:
        operations.create_app()

    msg = str(exc_info.value)
    assert "Multi-feature runtime cannot start with shared DATABASE_URL" in msg
    assert "c11-m1" in msg
    assert "NOTIFICATIONS_DATABASE_URL" in msg
    assert "c12-m1" in msg
    assert "PROCESS_ORCHESTRATION_DATABASE_URL" in msg


def test_multi_feature_runtime_refuses_when_one_feature_is_missing_own_url(monkeypatch):
    """If one feature has its dedicated URL but another lacks one, multi-feature runtime still refuses."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/shared.db")
    monkeypatch.setenv("NOTIFICATIONS_DATABASE_URL", "sqlite:////tmp/notif.db")

    with pytest.raises(ValueError) as exc_info:
        operations.create_app()

    msg = str(exc_info.value)
    assert "Multi-feature runtime cannot start with shared DATABASE_URL" in msg
    assert "c12-m1" in msg
    assert "PROCESS_ORCHESTRATION_DATABASE_URL" in msg
    assert "c11-m1" not in msg


def test_multi_feature_runtime_starts_when_all_features_have_dedicated_urls(monkeypatch):
    """When every feature has its own dedicated URL, multi-feature runtime starts even with DATABASE_URL set."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/shared.db")
    monkeypatch.setenv("NOTIFICATIONS_DATABASE_URL", "sqlite:////tmp/notif.db")
    monkeypatch.setenv("PROCESS_ORCHESTRATION_DATABASE_URL", "sqlite:////tmp/proc.db")

    test_app = operations.create_app()
    assert test_app is not None


def test_single_feature_runtime_accepts_plain_database_url(monkeypatch):
    """A single-feature runtime accepts DATABASE_URL as permitted by ADR-0003 decision 6."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/single.db")

    test_app = app.create_app(["registration"])
    assert test_app is not None


def test_runtime_without_database_url_uses_in_memory_databases():
    """Without DATABASE_URL set, multi-feature runtime starts with private in-memory databases."""
    test_app = operations.create_app()
    assert test_app is not None

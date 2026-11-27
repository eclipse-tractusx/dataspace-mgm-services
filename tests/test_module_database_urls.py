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
"""Every module of an installation (one process) has its own database: C2_M2_DATABASE_URL and C3_M1_DATABASE_URL.
DATABASE_URL (README 4) only counts for a module that has no own variable set, e.g. when it runs alone.
Found at the go-live of 06.11.2026: DATABASE_URL for C2-M2 switched C3-M1 to PostgreSQL as well."""
import pytest

from features.app_access.managers.config.config import Config
from portal_common import database

VARIABLES = ("DATABASE_URL", "C2_M2_DATABASE_URL", "C3_M1_DATABASE_URL", "COMPANY_PROFILE_DATABASE_URL",
             "C2_M2_CONFIG_FILE")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_the_database_of_c2_m2_does_not_switch_c3_m1(monkeypatch):
    monkeypatch.setenv("C2_M2_DATABASE_URL", "postgresql://u@db/c2_m2")
    assert Config().from_properties("database.url") == "postgresql://u@db/c2_m2"
    assert database.url("c3-m1") == database.IN_MEMORY


def test_each_module_takes_its_own_variable_before_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u@db/shared")
    monkeypatch.setenv("C2_M2_DATABASE_URL", "postgresql://u@db/c2_m2")
    monkeypatch.setenv("C3_M1_DATABASE_URL", "postgresql://u@db/c3_m1")
    assert Config().from_properties("database.url") == "postgresql://u@db/c2_m2"
    assert database.url("c3-m1") == "postgresql+pg8000://u@db/c3_m1"


def test_a_module_running_alone_still_takes_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u@db/alone")
    assert Config().from_properties("database.url") == "postgresql://u@db/alone"
    assert database.url("c3-m1") == "postgresql+pg8000://u@db/alone"

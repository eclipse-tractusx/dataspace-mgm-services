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
#  Assisted-By: Hermes Agent (deepseek-v4.1-flash)
#################################################################################
"""The database of the company profile (README 4, 5; F17): the SQLModel tables of the feature on the URL that
`portal_common.database` reads at call time, a private in-memory SQLite database when none is set.

The live tests run the same repository against a PostgreSQL server and are skipped without it:

    docker run --rm -d -p 55432:5432 -e POSTGRES_PASSWORD=pg -e POSTGRES_DB=company_profile postgres:16
    TEST_DATABASE_URL=postgresql://postgres:pg@localhost:55432/company_profile \
        uv run pytest -q tests/test_c3_m1_store_backend.py
"""
import os

import pytest

from features import company_profile
from features.company_profile.managers import company_repository
from portal_common import database

MODULE = "c3-m1"
VARIABLES = database.variables(MODULE)

COMPANY = {
    "id": "c0000001-0000-4000-8000-000000000001", "name": "Beispiel Maschinenbau GmbH",
    "street": "Musterstraße 1", "city": "Stuttgart", "country_code": "DE",
    "status": "REQUESTED", "core_data_source": "EBW", "bpn": "BPNLIUK2REMLK3F4",
}


@pytest.fixture(autouse=True)
def _no_database_variables(monkeypatch):
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    yield
    database.dispose()
    company_profile.reset()


@pytest.fixture
def postgres_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    return url


@pytest.fixture
def postgres(monkeypatch, postgres_url):
    monkeypatch.setenv("C3_M1_DATABASE_URL", postgres_url)
    assert database.engine(MODULE).dialect.name == "postgresql"
    company_repository.reset()
    yield company_repository
    company_repository.reset()


def test_the_default_database_is_in_memory():
    assert database.url(MODULE) == database.IN_MEMORY
    assert database.engine(MODULE).dialect.name == "sqlite"


def test_the_variables_are_the_feature_the_spec_id_and_database_url():
    assert VARIABLES == ["COMPANY_PROFILE_DATABASE_URL", "C3_M1_DATABASE_URL", "DATABASE_URL"]


def test_the_database_follows_the_variables_at_call_time(monkeypatch):
    """No value at import: the environment decides per call (AGENTS.md 6)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u@db/alone")
    assert database.url(MODULE) == "postgresql+pg8000://u@db/alone"
    monkeypatch.setenv("C3_M1_DATABASE_URL", "postgresql://u@db/c3_m1")
    assert database.url(MODULE) == "postgresql+pg8000://u@db/c3_m1"
    monkeypatch.delenv("C3_M1_DATABASE_URL")
    monkeypatch.delenv("DATABASE_URL")
    assert database.url(MODULE) == database.IN_MEMORY


def test_the_tables_are_only_in_the_feature_metadata():
    tables = set(database.metadata(MODULE).tables)
    assert {"company", "company_identifier", "company_role_assignment", "consent", "change_request",
            "change_request_document", "used_attestation", "audit_log"} <= tables
    other = database.metadata("c1-m2")
    assert other is not database.metadata(MODULE)
    assert all(database.metadata(MODULE).tables[name] is not other.tables.get(name) for name in tables)


def test_a_file_database_keeps_the_rows_across_engines(monkeypatch, tmp_path):
    monkeypatch.setenv("COMPANY_PROFILE_DATABASE_URL", f"sqlite:///{tmp_path / 'company_profile.db'}")
    company_repository.reset()
    company_repository.create_company(dict(COMPANY))
    database.dispose()
    assert company_repository.get_company(COMPANY["id"])["name"] == COMPANY["name"]


def test_on_startup_keeps_the_rows_and_seeds_once(monkeypatch, tmp_path):
    """The start creates missing tables only; a second start neither empties nor duplicates the seed."""
    monkeypatch.setenv("COMPANY_PROFILE_DATABASE_URL", f"sqlite:///{tmp_path / 'company_profile.db'}")
    company_repository.reset()
    company_repository.create_company(dict(COMPANY))
    company_profile.on_startup()
    company_profile.on_startup()
    assert company_repository.get_company(COMPANY["id"]) is not None
    assert company_repository.find_companies(size=100)[1] == 2     # the company and the OSP company


def test_an_unknown_id_is_not_found_in_memory():
    company_repository.reset()
    assert company_repository.get_company("nope") is None
    assert company_repository.update_company("nope", name="x") is None


def test_the_database_is_the_module_own_database(postgres):
    """The repository answers the same functions on PostgreSQL as on SQLite."""
    created = postgres.create_company(dict(COMPANY))
    assert created["bpn"] == "BPNLIUK2REMLK3F4"
    assert postgres.get_company(COMPANY["id"])["name"] == "Beispiel Maschinenbau GmbH"
    items, total = postgres.find_companies(status=["REQUESTED"])
    assert total == 1 and items[0]["id"] == COMPANY["id"]


def test_the_database_keeps_the_invariants(postgres):
    postgres.create_company(dict(COMPANY))
    with pytest.raises(ValueError):
        postgres.create_company(dict(COMPANY, id="c0000002-0000-4000-8000-000000000002",
                                     bpn="BPNLIUK2REMLK3F4"))
    with pytest.raises(ValueError):
        postgres.create_company(dict(COMPANY, id="c0000003-0000-4000-8000-000000000003",
                                     status="DELETED"))


def test_an_unknown_or_malformed_id_is_not_found(postgres):
    assert postgres.get_company("nope") is None
    assert postgres.update_company("nope", name="x") is None
    assert postgres.get_change_request("nope") is None


def test_the_lock_is_held_on_postgres(postgres):
    with postgres.lock(COMPANY["id"]) as locked:
        assert locked == COMPANY["id"]


def test_reset_empties_the_tables(postgres):
    postgres.create_company(dict(COMPANY))
    postgres.audit(COMPANY["id"], "sub-1", "updateCompany")
    postgres.reset()
    assert postgres.get_company(COMPANY["id"]) is None
    assert postgres.list_audit() == []

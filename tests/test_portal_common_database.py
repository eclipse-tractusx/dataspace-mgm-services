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
"""`portal_common.database`: one database per feature with SQLModel tables (ADR-0003, decision 6)."""
import pytest
from sqlmodel import Field, select

from portal_common import database
from portal_common.models import ApiModel

A, B = "c3-m1", "c1-m2"   # two features: company_profile, registration


class CompanyRow(database.table_base(A), table=True):
    __tablename__ = "test_company"
    company_id: str = Field(primary_key=True)
    legal_name: str


class ApplicationRow(database.table_base(B), table=True):
    __tablename__ = "test_application"
    application_id: str = Field(primary_key=True)


class Company(ApiModel):
    company_id: str
    legal_name: str


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    for module in (A, B):
        for name in database.variables(module):
            monkeypatch.delenv(name, raising=False)
    database.dispose()
    yield
    database.dispose()


def test_each_feature_has_its_own_tables_and_database():
    # the features' own tables sit next to the test tables, each in its own MetaData only
    assert "test_company" in database.metadata(A).tables
    assert "test_application" in database.metadata(B).tables
    # two features may use the same table name (both keep an `audit_log`): they are different tables in
    # different MetaData, created in different databases
    assert database.metadata(A) is not database.metadata(B)
    assert "test_company" not in database.metadata(B).tables and "test_application" not in database.metadata(A).tables
    assert database.engine(A) is not database.engine(B)


def test_rows_round_trip_and_convert_to_api_models():
    database.reset_tables(A)
    with database.session(A) as session:
        session.add(CompanyRow(company_id="c1", legal_name="ACME"))
    with database.session(A) as session:
        row = session.exec(select(CompanyRow)).one()
    assert Company.model_validate(row, from_attributes=True).to_json() == {"companyId": "c1", "legalName": "ACME"}


def test_an_error_rolls_the_unit_of_work_back():
    database.reset_tables(A)
    with pytest.raises(RuntimeError), database.session(A) as session:
        session.add(CompanyRow(company_id="c1", legal_name="ACME"))
        session.flush()
        raise RuntimeError("boom")
    with database.session(A) as session:
        assert session.exec(select(CompanyRow)).all() == []


def test_reset_empties_only_the_own_tables():
    database.reset_tables(A)
    database.reset_tables(B)
    with database.session(B) as session:
        session.add(ApplicationRow(application_id="a1"))
    database.reset_tables(A)
    with database.session(B) as session:
        assert len(session.exec(select(ApplicationRow)).all()) == 1


def test_the_url_is_read_in_order_at_call_time(monkeypatch):
    assert database.url(A) == database.IN_MEMORY
    monkeypatch.setenv("DATABASE_URL", "sqlite:///plain.db")
    assert database.url(A) == "sqlite:///plain.db"
    monkeypatch.setenv("C3_M1_DATABASE_URL", "postgresql://u@h/c3_m1")
    assert database.url(A) == "postgresql+pg8000://u@h/c3_m1"
    monkeypatch.setenv("COMPANY_PROFILE_DATABASE_URL", "postgres://u@h/company_profile")
    assert database.url(A) == "postgresql+pg8000://u@h/company_profile"
    assert database.variables(A)[0] == "COMPANY_PROFILE_DATABASE_URL"

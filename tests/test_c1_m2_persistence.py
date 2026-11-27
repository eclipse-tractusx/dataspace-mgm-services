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
"""C1-M2 keeps its state in its own database (rule F17): the tables of the feature, the terms seeded once,
the state kept across a new engine, and in-process callers before `on_startup()`."""
import pytest

from features import registration
from features.registration import interface
from features.registration.managers import agreement_repository, application_repository
from features.registration.models import tables
from features.registration.models.tables import ApplicationRow
from portal_common import database

VARIABLES = ("REGISTRATION_DATABASE_URL", "C1_M2_DATABASE_URL", "DATABASE_URL", "CATALOG_FILE")


@pytest.fixture(autouse=True)
def own_database(monkeypatch, tmp_path):
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("REGISTRATION_DATABASE_URL", f"sqlite:///{tmp_path / 'registration.db'}")
    database.dispose()
    yield
    database.dispose()


def _row(application_id: str = "a1") -> ApplicationRow:
    return ApplicationRow(id=application_id, seq=1, company_id="c1", applicant_sub="erika", status="CREATED",
                          kind="ONBOARDING", verification="DOCUMENTS", existing_company=False,
                          applicant={"sub": "erika", "givenName": "Erika", "familyName": "Mustermann"},
                          company_data={"legalName": "Beispiel GmbH", "address": {"countryCode": "DE"},
                                        "identifiers": []},
                          company_roles=["ACTIVE_PARTICIPANT"], created_at="2026-01-01T00:00:00+00:00",
                          changed_at="2026-01-01T00:00:00+00:00")


def test_the_tables_belong_to_the_feature():
    assert tables.Table.metadata is database.metadata(registration.MODULE)
    assert {"application", "application_document", "used_attestation", "audit_log",
            "agreement_version"} <= set(database.metadata(registration.MODULE).tables)


def test_state_outlives_the_engine_and_the_terms_are_seeded_once():
    registration.reset()
    application_repository.save(_row())
    seeded = len(agreement_repository.versions())
    database.dispose()                      # a new process would open a new engine
    registration.on_startup()
    assert application_repository.get("a1").company_data["legalName"] == "Beispiel GmbH"
    assert len(agreement_repository.versions()) == seeded > 0


def test_an_in_process_query_before_the_start_creates_the_tables():
    assert interface.list_applications_internal(applicationId=["unknown"]) == []
    assert interface.list_agreements_internal()


def test_the_internal_list_keeps_the_requested_order():
    registration.reset()
    application_repository.save(_row("a1"))
    application_repository.save(_row("a2").model_copy(update={"seq": 2}))
    assert [x["id"] for x in interface.list_applications_internal(applicationId=["a2", "x", "a1"])] == ["a2", "a1"]

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
#  SPDX-License-Identifier: Apache-2.0
#################################################################################
"""Tests of the C2-M2 DAOs on the SQLModel tables (private in-memory database) and of TestIamPortalIamAdapter."""
from __future__ import annotations

import datetime as dt

from c2_m2_database import _empty_c2_m2_database  # noqa: F401 - autouse: empty tables with a database
from features.app_access.models.common import Actor
from features.app_access.models.constants import (
    BindingStatus,
    CompanyStatus,
    InstanceClientStatus,
    InstanceKind,
    InvitationKind,
    JoinedVia,
)
from features.app_access.managers.config import Config
from features.app_access.managers.dao import sql_dao_service
from features.app_access.managers.iam.test_iam_portal_iam import TestIamPortalIamAdapter
from features.app_access.models.internal import (
    SuspendedRoles,
    AppClientTemplate,
    AppInstanceClient,
    AuditLogEntry,
    Company,
    CompanyUser,
    Invitation,
    RoleAssignmentLogEntry,
)
from tools import test_iam


def test_sql_company_dao():
    dao = sql_dao_service()
    cid = "c0000001-0000-4000-8000-000000000001"
    assert dao.companies.get(cid) is None

    company = Company(company_id=cid, bpn="BPNL000000000001", status=CompanyStatus.ACTIVE)
    dao.companies.save(company)

    fetched = dao.companies.get(cid)
    assert fetched is not None
    assert fetched.company_id == cid
    assert fetched.bpn == "BPNL000000000001"
    assert fetched.status == CompanyStatus.ACTIVE

    with dao.lock(("company", cid)):
        company.status = CompanyStatus.DISABLED
        dao.companies.save(company)

    assert dao.companies.get(cid).status == CompanyStatus.DISABLED


def test_sql_company_user_dao():
    dao = sql_dao_service()
    uid = "u0000001-0000-4000-8000-000000000001"
    cid = "c0000001-0000-4000-8000-000000000001"
    assert dao.company_users.current_of(uid) is None

    binding = CompanyUser(user_id=uid, company_id=cid, joined_via=JoinedVia.ONBOARDING)
    dao.company_users.save(binding)

    curr = dao.company_users.current_of(uid)
    assert curr is not None
    assert curr.user_id == uid
    assert curr.status == BindingStatus.ACTIVE

    list_user = dao.company_users.list_of(uid, cid)
    assert len(list_user) == 1

    list_comp = dao.company_users.list_of_company(cid, [BindingStatus.ACTIVE])
    assert len(list_comp) == 1

    with dao.lock(("account", uid)):
        binding.status = BindingStatus.REMOVED
        dao.company_users.save(binding)

    assert dao.company_users.current_of(uid) is None


def test_sql_app_client_daos():
    dao = sql_dao_service()
    app_id = "app-001"
    assert dao.templates.get(app_id) is None

    tpl = AppClientTemplate(
        app_id=app_id,
        provider_company_id="prov-001",
        app_name="Test App",
        iam_client_id="client-tpl-001",
        iam_client_uuid="uuid-001",
    )
    dao.templates.save(tpl)
    assert dao.templates.get(app_id).iam_client_uuid == "uuid-001"

    ic = AppInstanceClient(
        id="ic-001",
        app_id=app_id,
        instance_kind=InstanceKind.SINGLE,
        status=InstanceClientStatus.ACTIVE,
        offer_subscription_id="sub-001",
        customer_company_id="cust-001",
        iam_client_id="client-001",
        instance_url="https://instance.example.com",
        iam_client_uuid="uuid-client-001",
    )
    dao.instance_clients.save(ic)
    assert dao.instance_clients.get(ic.id) is not None
    assert dao.instance_clients.find_by_subscription("sub-001") is not None
    assert dao.instance_clients.find_single(app_id) is not None
    assert dao.instance_clients.find_by_iam_client_id("client-001") is not None
    assert len(dao.instance_clients.list_of_app(app_id)) == 1
    assert len(dao.instance_clients.list_all()) == 1

    num1 = dao.instance_clients.next_client_number()
    num2 = dao.instance_clients.next_client_number()
    assert num2 == num1 + 1


def test_sql_invitation_dao():
    dao = sql_dao_service()
    inv = Invitation(
        kind=InvitationKind.STAFF,
        company_id=None,
        given_name="Alice",
        family_name="Smith",
        roles=["OSP Admin"],
        code_hash="abc123hash",
        expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        created_by="system",
    )
    dao.invitations.save(inv)
    assert dao.invitations.get(inv.id) is not None
    assert dao.invitations.find_by_code_hash("abc123hash") is not None
    assert len(dao.invitations.list_of(InvitationKind.STAFF, None)) == 1
    assert len(dao.invitations.list_all()) == 1


def test_sql_logs_daos():
    dao = sql_dao_service()
    audit_entry = AuditLogEntry(actor=Actor.system(), operation="test", company_id="c1", object_id="obj1")
    dao.audit_log.add(audit_entry)
    assert len(dao.audit_log.list_all()) == 1

    role_entry = RoleAssignmentLogEntry(
        user_id="u1",
        company_id="c1",
        role_kind="COMPANY_PORTAL",
        iam_client_id="portal-core",
        role_name="Company Admin",
        action="ADDED",
        actor=Actor.system(),
        operation="assign-company-admin",
    )
    dao.role_log.add(role_entry)
    assert len(dao.role_log.list_all()) == 1


def test_test_iam_portal_iam_adapter():
    test_iam.reset()
    cfg = Config()
    adapter = TestIamPortalIamAdapter(cfg)

    # Core client and role inspection
    client = adapter.find_client("portal-core")
    assert client is not None
    roles = adapter.client_roles(client["id"])
    assert any(r["name"] == "Company Admin" for r in roles)

    # User lifecycle via adapter
    uid = "test-user-adapter"
    test_iam.iam().first_login(uid, "Alice", "Tester")
    user = adapter.get_user(uid)
    assert user is not None
    assert user["firstName"] == "Alice"
    assert user["lastName"] == "Tester"

    # Update company attributes
    cid = "c0000001-0000-4000-8000-000000000001"
    adapter.update_user(uid, {"attributes": {"company_id": [cid], "bpn": ["BPNL123456789012"]}})
    updated = adapter.get_user(uid)
    assert updated["attributes"]["company_id"] == [cid]
    assert updated["attributes"]["bpn"] == ["BPNL123456789012"]

    # Role mappings
    adapter.add_client_role_mappings(uid, adapter.CORE_UUID, [{"name": "Company Admin"}])
    mappings = adapter.client_role_mappings(uid, adapter.CORE_UUID)
    assert any(r["name"] == "Company Admin" for r in mappings)

    adapter.remove_client_role_mappings(uid, adapter.CORE_UUID, [{"name": "Company Admin"}])
    mappings_after = adapter.client_role_mappings(uid, adapter.CORE_UUID)
    assert not any(r["name"] == "Company Admin" for r in mappings_after)


def test_records_survive_the_round_trip_through_the_tables():
    """Value sets, JSON columns and aware timestamps come back as they were saved."""
    dao = sql_dao_service()
    binding = CompanyUser(user_id="u9", company_id="c9", joined_via=JoinedVia.ONBOARDING,
                          status=BindingStatus.DISABLED,
                          suspended_roles=SuspendedRoles(["Company Admin"], [("app-1", "Viewer")]))
    dao.company_users.save(binding)
    assert dao.company_users.current_of("u9") == binding
    actor = Actor.process({"processId": "p1", "stepRunId": "s1"})
    dao.audit_log.add(AuditLogEntry(actor=actor, operation="op", company_id="c9", object_id=None))
    assert dao.audit_log.list_all()[0].actor == actor


def test_the_initial_migration_creates_the_tables_of_the_models(tmp_path, monkeypatch):
    """`managers/migrations` (PostgreSQL) and `models/tables.py` (SQLite) describe the same schema."""
    from alembic import command
    from alembic.autogenerate import compare_metadata
    from alembic.config import Config as AlembicConfig
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    from features.app_access.managers.database import MIGRATIONS_DIR, VERSION_TABLE
    from portal_common import database

    url = f"sqlite:///{tmp_path / 'c2_m2.db'}"
    monkeypatch.setenv("C2_M2_DATABASE_URL", url)
    config = AlembicConfig()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    command.upgrade(config, "head")
    with create_engine(url).connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), database.metadata("c2-m2"))
    assert [d for d in diff if not (d[0] == "remove_table" and d[1].name == VERSION_TABLE)] == []

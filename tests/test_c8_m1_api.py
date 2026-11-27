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
"""C8-M1 Offers (feature `offers`): the core path over HTTP under `/api/offers` (token, permission, company
scope, `OfferApproved`), the old base path `/api/c8-m1` answering 404, and the in-process interface."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import BASE, bearer
from features import offers
from features.offers import interface
from features.offers.managers import neighbour_client
from portal_common import events, layout, spec
from portal_common import http as phttp
from portal_common.problems import Problem
from scaffold import app as scaffold_app
from tools import test_iam

PROVIDER = "c0000002-0000-4000-8000-000000000002"
OTHER = "c0000001-0000-4000-8000-000000000001"
BASE_PATH = "/api/offers"
COMPANY_ROLES = {PROVIDER: ["APP_PROVIDER"], OTHER: ["SERVICE_PROVIDER"]}


@pytest.fixture(autouse=True)
def _companies(monkeypatch):
    monkeypatch.setattr(neighbour_client, "query_company",
                        lambda company_id: {"companyId": company_id, "companyRoles": COMPANY_ROLES.get(company_id, [])})


@pytest.fixture
def client():
    app = scaffold_app.create_app()
    phttp.register_local(BASE, app)
    yield TestClient(app, base_url=BASE)
    scaffold_app.reset_all(app.state.entries)


def _person(key: str, company_id: str, bpn: str) -> dict:
    iam = test_iam.iam()
    uid = iam.find(key)
    iam.add_portal_roles(uid, ["Company Admin"])
    iam.bind(uid, company_id, bpn)
    return bearer(iam.person_token(uid))


@pytest.fixture
def hans():
    return _person("hans", PROVIDER, "BPNL00000000U2LG")


@pytest.fixture
def erika():
    return _person("erika", OTHER, "BPNLIUK2REMLK3F4")


@pytest.fixture
def otto():
    return bearer(test_iam.iam().person_token(test_iam.iam().find("otto")))


def _create(client, headers, **body) -> dict:
    reply = client.post(f"{BASE_PATH}/offers", headers=headers, json={"offerType": "APP", "name": "Demo App"} | body)
    assert reply.status_code == 201, reply.text
    return reply.json()


def test_feature_is_served_under_its_readable_name():
    assert (offers.NAME, offers.MODULE) == ("offers", "c8-m1")
    assert layout.base_path("c8-m1") == BASE_PATH == spec.module("c8-m1").base_path
    assert layout.interface_package("c8-m1") == "features.offers.interface"


def test_old_base_path_answers_404(client, hans):
    assert client.post("/api/c8-m1/offers", headers=hans, json={"offerType": "APP", "name": "x"}).status_code == 404
    assert client.get("/api/c8-m1/internal/offers/x").status_code == 404


def test_core_path_create_roles_profile_submit_approve(client, hans, otto):
    offer = _create(client, hans)
    assert offer["status"] == "DRAFT" and offer["providerCompanyId"] == PROVIDER and offer["instanceKind"] == "MULTI"
    oid = offer["offerId"]

    roles = client.put(f"{BASE_PATH}/offers/{oid}/roles", headers=hans, json=[{"name": "Viewer"}, {"name": "Editor"}])
    assert roles.status_code == 200 and [r["name"] for r in roles.json()] == ["Viewer", "Editor"]
    profile = client.put(f"{BASE_PATH}/offers/{oid}/technical-user-profile", headers=hans,
                         json={"name": "sync", "roles": [{"name": "Dataspace Discovery"}]})
    assert profile.status_code == 200 and profile.json()["roles"] == [{"name": "Dataspace Discovery"}]

    submitted = client.post(f"{BASE_PATH}/offers/{oid}/submit", headers=hans)
    assert submitted.status_code == 200 and submitted.json()["status"] == "IN_REVIEW"
    assert client.post(f"{BASE_PATH}/offers/{oid}/submit", headers=hans).json()["type"] == \
        "urn:c8-m1:problem:invalid-state"

    approved = client.post(f"{BASE_PATH}/osp/offers/{oid}/approve", headers=otto)
    assert approved.status_code == 200 and approved.json()["status"] == "ACTIVE"
    published = [e for e in events.RELAY.log if e["type"] == "OfferApproved"]
    assert published[-1]["data"] == {"offerId": oid, "offerType": "APP", "providerCompanyId": PROVIDER}
    assert published[-1]["source"] == "urn:c8-m1"
    assert client.get(f"{BASE_PATH}/offers/{oid}", headers=hans).json()["status"] == "ACTIVE"


def test_create_checks_body_and_company_role(client, hans, erika):
    invalid = client.post(f"{BASE_PATH}/offers", headers=hans, json={"offerType": "DATA", "name": "x"})
    assert invalid.status_code == 400 and invalid.json()["type"] == "urn:c8-m1:problem:validation"
    missing = client.post(f"{BASE_PATH}/offers", headers=erika, json={"offerType": "APP", "name": "x"})
    assert missing.status_code == 403 and missing.json()["type"] == "urn:c8-m1:problem:company-role-missing"
    service = _create(client, erika, offerType="SERVICE")
    assert service["instanceKind"] is None


def test_an_app_without_roles_is_incomplete_and_unknown_offers_are_404(client, hans, otto):
    oid = _create(client, hans)["offerId"]
    incomplete = client.post(f"{BASE_PATH}/offers/{oid}/submit", headers=hans)
    assert incomplete.status_code == 409 and incomplete.json()["type"] == "urn:c8-m1:problem:incomplete"
    not_in_review = client.post(f"{BASE_PATH}/osp/offers/{oid}/approve", headers=otto)
    assert not_in_review.status_code == 409
    assert client.post(f"{BASE_PATH}/osp/offers/unknown/approve", headers=otto).status_code == 404
    bad_profile = client.put(f"{BASE_PATH}/offers/{oid}/technical-user-profile", headers=hans, json={"name": "x"})
    assert bad_profile.status_code == 400


def test_company_scope_hides_offers_of_another_company(client, hans, erika):
    oid = _create(client, hans)["offerId"]
    assert client.get(f"{BASE_PATH}/offers/{oid}", headers=erika).status_code == 404
    assert client.put(f"{BASE_PATH}/offers/{oid}/roles", headers=erika, json=[{"name": "x"}]).status_code == 404
    assert client.post(f"{BASE_PATH}/offers/{oid}/submit", headers=erika).status_code == 404
    assert client.get(f"{BASE_PATH}/offers/unknown", headers=hans).status_code == 404


def test_permissions_are_checked(client, hans, erika):
    assert client.post(f"{BASE_PATH}/offers", json={"offerType": "APP", "name": "x"}).status_code == 401
    oid = _create(client, hans)["offerId"]
    assert client.post(f"{BASE_PATH}/osp/offers/{oid}/approve", headers=hans).status_code == 403
    assert client.get(f"{BASE_PATH}/internal/offers/{oid}", headers=hans).status_code == 403


def test_internal_lookup_over_http(client, hans):
    oid = _create(client, hans)["offerId"]
    svc = bearer(test_iam.iam().client_token("svc-c12-m1"))
    found = client.get(f"{BASE_PATH}/internal/offers/{oid}", headers=svc)
    assert found.status_code == 200 and found.json()["hasTechnicalUserProfile"] is False
    missing = client.get(f"{BASE_PATH}/internal/offers/unknown", headers=svc)
    assert missing.status_code == 404 and missing.json()["type"] == "urn:c8-m1:problem:not-found"


def test_spec_operations_without_a_controller_answer_from_the_fallback(client, hans):
    assert client.get(f"{BASE_PATH}/offers", headers=hans).status_code == 501


def test_interface_lookup_and_stand_in_functions(client, hans):
    oid = _create(client, hans)["offerId"]
    client.put(f"{BASE_PATH}/offers/{oid}/technical-user-profile", headers=hans,
               json={"name": "sync", "roles": [{"name": "Dataspace Discovery"}]})
    offer = interface.get_offer_internal(offerId=oid)
    assert offer["offerId"] == oid and offer["hasTechnicalUserProfile"] is True
    with pytest.raises(Problem) as unknown:
        interface.get_offer_internal(offerId="unknown")
    assert unknown.value.status == 404
    interface.reset()
    with pytest.raises(Problem):
        interface.get_offer_internal(offerId=oid)
    with pytest.raises(AttributeError):
        interface.no_such_function   # noqa: B018


def test_wire_format_keeps_the_field_names_and_nulls(client, hans):
    offer = _create(client, hans, privacyPolicies=["COMPANY_DATA"])
    assert list(offer) == ["offerId", "status", "offerType", "name", "providerCompanyId", "instanceKind",
                           "instanceUrl", "roles", "technicalUserProfile", "agreements"]
    assert offer["technicalUserProfile"] is None and offer["instanceUrl"] is None and offer["roles"] == []
    internal = interface.get_offer_internal(offerId=offer["offerId"])
    assert internal == offer | {"hasTechnicalUserProfile": False}


def test_offers_live_in_the_feature_database(client, hans):
    from features.offers.models.tables import OfferRow
    from portal_common import database

    oid = _create(client, hans)["offerId"]
    with database.session(offers.MODULE) as session:
        assert session.get(OfferRow, oid).provider_company_id == PROVIDER
    offers.reset()
    with database.session(offers.MODULE) as session:
        assert session.get(OfferRow, oid) is None

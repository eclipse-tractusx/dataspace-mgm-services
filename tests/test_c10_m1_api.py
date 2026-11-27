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
"""C10-M1 over HTTP under `/api/subscriptions` (the old `/api/c10-m1` answers 404) and the in-process interface:
provider configuration, subscribe, visibility, start setup, activate, the steps and the queries of section 9."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import BASE, bearer
from features.subscriptions import interface
from features.subscriptions.managers import neighbour_client, provider_configuration_repository, subscription_repository
from portal_common import events
from portal_common import http as phttp
from portal_common.problems import Problem
from scaffold import app as scaffold_app
from tools import provider_double, test_iam

CUSTOMER = "c0000001-0000-4000-8000-000000000001"
PROVIDER = "c0000002-0000-4000-8000-000000000002"
OTHER = "c0000003-0000-4000-8000-000000000003"
OFFER = "0ffe0001-0000-4000-8000-000000000001"
BASE_PATH = "/api/subscriptions"
PROVIDER_SYSTEM = f"{BASE}/test-tools/provider"
CONFIGURATION = {"setupUrl": f"{PROVIDER_SYSTEM}/setup", "callbackUrl": f"{PROVIDER_SYSTEM}/callback",
                 "tokenUrl": f"{PROVIDER_SYSTEM}/token", "clientId": provider_double.CLIENT_ID,
                 "clientSecret": provider_double.CLIENT_SECRET}


@pytest.fixture
def neighbours(monkeypatch):
    """C8-M1, C12-M1, C3-M1 and C2-M3 as the subscriptions see them."""
    state = {"offer": {"offerId": OFFER, "status": "ACTIVE", "offerType": "APP", "instanceKind": "MULTI",
                       "providerCompanyId": PROVIDER},
             "processes": [], "rotated": []}
    monkeypatch.setattr(neighbour_client, "get_offer_internal",
                        lambda offer_id: state["offer"] if offer_id == OFFER else None)
    monkeypatch.setattr(neighbour_client, "find_processes_of_subscription", lambda sid: state["processes"])
    monkeypatch.setattr(neighbour_client, "query_company",
                        lambda cid: {"name": "Beispiel Maschinenbau GmbH", "address": {"countryCode": "DE"}})

    def rotate(technical_user_id, offer_subscription_id):
        state["rotated"].append((technical_user_id, offer_subscription_id))
        return {"iamClientId": f"sa-{technical_user_id}", "secret": "rotated-secret"}
    monkeypatch.setattr(neighbour_client, "rotate_subscription_credentials", rotate)
    return state


@pytest.fixture
def client(neighbours):
    app = scaffold_app.create_app()
    phttp.register_local(BASE, app)
    yield TestClient(app, base_url=BASE)
    scaffold_app.reset_all(app.state.entries)


def _person(key: str, company_id: str, role: str = "Company Admin") -> dict:
    iam = test_iam.iam()
    uid = iam.find(key)
    iam.add_portal_roles(uid, [role])
    iam.bind(uid, company_id, None)
    return bearer(iam.person_token(uid))


@pytest.fixture
def erika():
    return _person("erika", CUSTOMER)


@pytest.fixture
def pia():
    return _person("pia", PROVIDER)


@pytest.fixture
def hans():
    return _person("hans", OTHER)


def _service(module: str) -> dict:
    return bearer(test_iam.iam().client_token(f"svc-{module}"))


def _subscribe(client, erika) -> dict:
    created = client.post(f"{BASE_PATH}/subscriptions", headers=erika, json={"offerId": OFFER, "agreementConsents": []})
    assert created.status_code == 201, created.text
    return created.json()


def _types() -> list[str]:
    return [ev["type"] for ev in events.RELAY.log if ev["source"] == events.source_of("c10-m1")]


# ---------------------------------------------------------------- HTTP
def test_served_under_the_readable_name_only(client, erika):
    paths = client.get("/openapi.json").json()["paths"]
    assert f"{BASE_PATH}/subscriptions/{{offerSubscriptionId}}/activate" in paths
    assert f"{BASE_PATH}/steps/notify-provider" in paths
    assert not any(path.startswith("/api/c10-m1/") for path in paths)
    assert client.post("/api/c10-m1/subscriptions", headers=erika, json={"offerId": OFFER}).status_code == 404
    assert client.get("/api/c10-m1/subscriptions/x", headers=erika).status_code == 404


def test_provider_configuration_hides_the_secret(client, pia):
    stored = client.put(f"{BASE_PATH}/provider-configuration", headers=pia, json=CONFIGURATION)
    assert stored.status_code == 200, stored.text
    assert "clientSecret" not in stored.json() and stored.json()["setupUrl"] == CONFIGURATION["setupUrl"]
    assert stored.json()["companyId"] == PROVIDER and stored.json()["clientSecretSet"] is True
    assert provider_configuration_repository.get(PROVIDER).client_secret == provider_double.CLIENT_SECRET

    incomplete = client.put(f"{BASE_PATH}/provider-configuration", headers=pia, json={"setupUrl": "x"})
    assert incomplete.status_code == 400
    assert incomplete.json()["type"] == "urn:c10-m1:problem:validation"
    unknown = client.put(f"{BASE_PATH}/provider-configuration", headers=pia, json=CONFIGURATION | {"extra": 1})
    assert unknown.status_code == 400   # additionalProperties: false
    assert client.put(f"{BASE_PATH}/provider-configuration", json=CONFIGURATION).status_code == 401


def test_subscribe_and_visibility(client, erika, pia, hans):
    s = _subscribe(client, erika)
    assert s["status"] == "REQUESTED" and s["customerCompanyId"] == CUSTOMER and s["providerCompanyId"] == PROVIDER
    assert "SubscriptionRequested" in _types()

    sid = s["offerSubscriptionId"]
    for person in (erika, pia):
        seen = client.get(f"{BASE_PATH}/subscriptions/{sid}", headers=person)
        assert seen.status_code == 200 and seen.json()["setupStatus"] is None
    assert client.get(f"{BASE_PATH}/subscriptions/{sid}", headers=hans).status_code == 404   # another company


def test_subscribe_rejects_inactive_and_own_offers(client, erika, pia, neighbours):
    body = {"offerId": OFFER, "agreementConsents": []}
    own = client.post(f"{BASE_PATH}/subscriptions", headers=pia, json=body)
    assert own.status_code == 409 and own.json()["type"] == "urn:c10-m1:problem:own-offer"
    neighbours["offer"]["status"] = "INACTIVE"
    inactive = client.post(f"{BASE_PATH}/subscriptions", headers=erika, json=body)
    assert inactive.status_code == 409 and inactive.json()["type"] == "urn:c10-m1:problem:offer-not-active"
    unknown = client.post(f"{BASE_PATH}/subscriptions", headers=erika, json=body | {"offerId": OTHER})
    assert unknown.status_code == 409


def test_request_bodies_follow_the_spec(client, erika, pia):
    for wrong in ({"offerId": "nope", "agreementConsents": []}, {"offerId": OFFER},
                  {"offerId": OFFER, "agreementConsents": [], "extra": 1}):
        reply = client.post(f"{BASE_PATH}/subscriptions", headers=erika, json=wrong)
        assert reply.status_code == 400 and reply.json()["type"] == "urn:c10-m1:problem:validation", wrong
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    plain_http = client.post(f"{BASE_PATH}/subscriptions/{sid}/start-setup", headers=pia,
                             json={"instanceUrl": "http://app.example"})
    assert plain_http.status_code == 400   # InstanceUrl: https only
    assert client.post(f"{BASE_PATH}/subscriptions/{sid}/start-setup", headers=pia).status_code == 202   # no body


def test_start_setup_and_activate_follow_the_setup_process(client, erika, pia, neighbours):
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    url = f"{BASE_PATH}/subscriptions/{sid}"
    assert client.post(f"{url}/start-setup", headers=erika, json={}).status_code == 403   # customer, not provider
    assert client.post(f"{url}/activate", headers=pia).status_code == 409                 # still REQUESTED

    started = client.post(f"{url}/start-setup", headers=pia, json={"instanceUrl": "https://app.example"})
    assert started.status_code == 202 and started.json()["status"] == "PENDING"
    assert started.json()["instanceUrl"] == "https://app.example"
    assert client.post(f"{url}/start-setup", headers=pia, json={}).status_code == 409    # not REQUESTED any more

    neighbours["processes"][:] = [{"flowKey": "subscription-setup", "status": "RUNNING"}]
    running = client.post(f"{url}/activate", headers=pia)
    assert running.status_code == 409 and running.json()["type"] == "urn:c10-m1:problem:setup-not-finished"
    neighbours["processes"][:] = [{"flowKey": "subscription-setup", "status": "FAILED"}]
    assert client.post(f"{url}/activate", headers=pia).json()["type"] == "urn:c10-m1:problem:setup-failed"

    neighbours["processes"][:] = [{"flowKey": "subscription-setup", "status": "WAITING"}]
    activated = client.post(f"{url}/activate", headers=pia)
    assert activated.status_code == 200 and activated.json()["status"] == "ACTIVE"
    assert client.get(url, headers=erika).json()["setupStatus"] == "WAITING"
    assert _types() == ["SubscriptionRequested", "SubscriptionSetupStarted", "SubscriptionActivated"]


def test_steps_call_the_provider_system(client, erika, pia):
    client.put(f"{BASE_PATH}/provider-configuration", headers=pia, json=CONFIGURATION)
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    step = {"processId": "00000000-0000-4000-8000-000000000001", "stepRunId": "00000000-0000-4000-8000-000000000002",
            "offerSubscriptionId": sid}
    assert client.post(f"{BASE_PATH}/steps/notify-provider", headers=erika, json=step).status_code == 403

    notified = client.post(f"{BASE_PATH}/steps/notify-provider", headers=_service("c12-m1"), json=step)
    assert notified.status_code == 200, notified.text
    assert notified.json() == {"stepRunId": step["stepRunId"], "state": "DONE", "result": {}}
    setup = provider_double.calls[-1]
    assert setup["kind"] == "setup" and setup["body"]["customerName"] == "Beispiel Maschinenbau GmbH"
    assert setup["body"]["customerCountry"] == "DE" and setup["body"]["setupExpected"] is True

    callback = client.post(f"{BASE_PATH}/steps/send-activation-callback", headers=_service("c12-m1"),
                           json=step | {"clientId": "instance-client", "technicalUsers": [{"technicalUserId": "tu1"}]})
    assert callback.status_code == 200, callback.text
    body = provider_double.calls[-1]["body"]
    assert body["clientId"] == "instance-client"
    assert body["technicalUser"] == {"clientId": "sa-tu1", "clientSecret": "rotated-secret"}

    missing = client.post(f"{BASE_PATH}/steps/notify-provider", headers=_service("c12-m1"),
                          json=step | {"offerSubscriptionId": OTHER})
    assert missing.status_code == 404
    invalid = client.post(f"{BASE_PATH}/steps/notify-provider", headers=_service("c12-m1"),
                          json={"offerSubscriptionId": sid})
    assert invalid.status_code == 400   # processId and stepRunId are required


def test_internal_queries_are_served_by_the_fallback(client, erika):
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    found = client.get(f"{BASE_PATH}/internal/subscriptions/{sid}", headers=_service("c2-m3"))
    assert found.status_code == 200, found.text
    assert found.json()["offerType"] == "APP" and found.json()["providerCompanyId"] == PROVIDER


# ---------------------------------------------------------------- interface
def test_interface_queries(client, erika):
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    ref = {"offerSubscriptionId": sid, "offerId": OFFER, "customerCompanyId": CUSTOMER, "status": "REQUESTED"}
    assert interface.find_subscriptions(customerCompanyId=CUSTOMER) == [ref]
    assert interface.find_subscriptions(offerId=OFFER, status="REQUESTED") == [ref]
    assert interface.find_subscriptions(status=["ACTIVE", "PENDING"]) == []
    assert interface.find_subscriptions(customerCompanyId=OTHER) == []
    assert interface.find_subscriptions(customerCompanyId=CUSTOMER, page=0) == [ref]   # other parameters ignored

    internal = interface.get_subscription_internal(offerSubscriptionId=sid)
    assert internal == ref | {"offerType": "APP", "instanceKind": "MULTI", "providerCompanyId": PROVIDER,
                              "instanceUrl": None}
    with pytest.raises(Problem) as missing:
        interface.get_subscription_internal(offerSubscriptionId="unknown")
    assert missing.value.status == 404


def test_interface_steps_without_configuration(client, erika, neighbours):
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    step = {"processId": OTHER, "stepRunId": OFFER, "offerSubscriptionId": sid}
    with pytest.raises(Problem) as unconfigured:
        interface.notify_provider(step)
    assert unconfigured.value.status == 409
    # without a callbackUrl nothing is sent and no secret is rotated
    assert interface.send_activation_callback(step | {"technicalUsers": [{"technicalUserId": "tu1"}]}) == \
        {"stepRunId": OFFER, "state": "DONE", "result": {}}
    assert neighbours["rotated"] == []
    with pytest.raises(Problem) as missing:
        interface.send_activation_callback(step | {"offerSubscriptionId": OTHER})
    assert missing.value.status == 404
    with pytest.raises(Problem) as invalid:
        interface.notify_provider({"offerSubscriptionId": sid})
    assert invalid.value.status == 400


def test_interface_reset_and_standin_functions(client, erika, pia):
    client.put(f"{BASE_PATH}/provider-configuration", headers=pia, json=CONFIGURATION)
    sid = _subscribe(client, erika)["offerSubscriptionId"]
    assert subscription_repository.get(sid).status == "REQUESTED"
    interface.reset()
    assert subscription_repository.get(sid) is None and provider_configuration_repository.get(PROVIDER) is None
    assert interface.MODULE == "c10-m1"
    with pytest.raises(AttributeError):
        interface.no_such_function   # noqa: B018 - only the steps and queries of the spec exist

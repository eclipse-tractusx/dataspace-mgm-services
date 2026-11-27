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
"""Runtime split (ADR-0002, ADR-0003): runtimes made of features, module selection per pod and event
delivery between pods."""
from __future__ import annotations

import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient

from conftest import BASE, bearer
from features import company_profile, registration
from features.process_orchestration.services import event_hub
from portal_common import event_forwarder, events, layout, neighbours, tokens
from runtimes import __main__ as runtime_main
from runtimes import create_runtime, onboarding
from scaffold import registry


def test_registry_serves_only_enabled_features(monkeypatch):
    monkeypatch.setenv("ENABLED_FEATURES", "c1-m2, C3-M1")
    assert [e.id for e in registry.load()] == ["c1-m2", "c3-m1"]


def test_enabled_features_take_readable_names(monkeypatch):
    monkeypatch.setenv("ENABLED_FEATURES", "registration, company-profile, process_orchestration")
    assert [e.id for e in registry.load()] == ["c1-m2", "c3-m1", "c12-m1"]


def test_unknown_feature_names_fail_fast(monkeypatch):
    monkeypatch.setenv("ENABLED_FEATURES", "registration, onboardng")
    with pytest.raises(ValueError, match="onboardng"):
        registry.load()


def test_registry_serves_all_modules_by_default(monkeypatch):
    monkeypatch.delenv("ENABLED_FEATURES", raising=False)
    assert {"c1-m2", "c3-m1", "c12-m1"} <= {e.id for e in registry.load()}


@pytest.fixture(autouse=True)
def _environment():
    """A split runtime sets `<MODULE>_URL=in-process` for its features; keep that out of other tests."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


def _served(app) -> list[dict]:
    return TestClient(app, base_url=BASE).get("/scaffold/modules").json()


def test_feature_packages_are_found_by_their_readable_name():
    assert layout.features() == {
        "c1-m2": "registration",
        "c2-m2": "app_access",
        "c1-m3": "application_review",
        "c2-m3": "technical_user",
        "c3-m1": "company_profile",
        "c4-m1": "credentials",
        "c8-m1": "offers",
        "c3-m2": "csp_connection",
        "c11-m1": "notifications",
        "c6-m1": "connector",
        "c12-m1": "process_orchestration",
        "c4-m2": "dataspace_wallet_interface",
        "c10-m1": "subscriptions",
    }
    assert (registration.NAME, registration.MODULE) == ("registration", "c1-m2")
    assert (company_profile.NAME, company_profile.MODULE) == ("company_profile", "c3-m1")
    assert layout.interface_package("c3-m1") == "features.company_profile.interface"
    assert layout.interface_package("c12-m1") == "features.process_orchestration.interface"


def test_hybrid_runtime_serves_both_onboarding_features(monkeypatch):
    monkeypatch.setenv("ENABLED_FEATURES", "c12-m1")   # ignored: a runtime names its features in code
    monkeypatch.setenv("MODULE_URLS", '{"registration": "http://onboarding:8000", "company_profile": '
                                      '"http://onboarding:8000", "c12-m1": "http://process-orchestration:8000"}')
    assert _served(onboarding.create_app()) == [{"module": "c1-m2", "kind": "feature"},
                                                 {"module": "c3-m1", "kind": "feature"}]
    # the features of the pod call each other in-process; the others are neighbours over HTTP
    assert neighbours.in_process("c1-m2") and neighbours.in_process("c3-m1")
    assert neighbours.address("c12-m1") == "http://process-orchestration:8000"


def test_single_feature_runtime_serves_its_paths_only():
    client = TestClient(create_runtime(registration), base_url=BASE)
    assert client.get("/scaffold/modules").json() == [{"module": "c1-m2", "kind": "feature"}]
    paths = client.get("/openapi.json").json()["paths"]
    assert any(p.startswith("/api/registration/") for p in paths)
    assert not any(p.startswith("/api/company-profile/") for p in paths)


def test_a_feature_is_served_under_its_readable_name_and_no_longer_under_its_spec_id():
    assert layout.base_path("c1-m2") == "/api/registration"
    assert layout.base_path("c3-m1") == "/api/company-profile"
    assert layout.base_path("c12-m1") == "/api/process-orchestration"
    paths = TestClient(create_runtime(registration, company_profile, "process_orchestration"),
                       base_url=BASE).get("/openapi.json").json()["paths"]
    prefixes = {"/".join(path.split("/")[:3]) for path in paths if path.startswith("/api/")}
    assert {"/api/registration", "/api/company-profile", "/api/process-orchestration"} <= prefixes
    assert not prefixes & {"/api/c1-m2", "/api/c3-m1", "/api/c12-m1"}


def test_runtime_mixes_features_and_modules_not_migrated_yet():
    assert [e["module"] for e in _served(create_runtime(company_profile, "process_orchestration"))] == ["c3-m1", "c12-m1"]


def test_runtime_name_selects_a_runtime_or_a_feature():
    assert runtime_main.factory("onboarding") == "runtimes.onboarding:create_app"
    assert runtime_main.factory("installation") == "runtimes.installation:create_app"
    assert runtime_main.factory("company-profile") == "features.company_profile.main:create_app"
    assert runtime_main.factory("marketplace") == "runtimes.marketplace:create_app"
    assert runtime_main.factory("connectivity") == "runtimes.connectivity:create_app"
    assert runtime_main.factory("security") == "runtimes.security:create_app"
    assert runtime_main.factory("operations") == "runtimes.operations:create_app"
    with pytest.raises(SystemExit, match="unknown runtime"):
        runtime_main.factory("onboardng")


def test_domain_runtimes_serve_their_respective_clusters():
    from runtimes import connectivity, marketplace, operations, security

    assert {e["module"] for e in _served(marketplace.create_app())} == {"c8-m1", "c10-m1"}
    assert {e["module"] for e in _served(connectivity.create_app())} == {"c3-m2", "c6-m1"}
    assert {"c2-m3", "c4-m1"} <= {e["module"] for e in _served(security.create_app())}
    assert {"c11-m1", "c12-m1"} <= {e["module"] for e in _served(operations.create_app())}


def test_module_urls_take_readable_feature_names(monkeypatch):
    monkeypatch.delenv("C3_M1_URL", raising=False)
    monkeypatch.setenv("MODULE_URLS", '{"company_profile": "http://onboarding:8000", "c1-m2": "in-process"}')
    assert neighbours.address("c3-m1") == "http://onboarding:8000"
    assert neighbours.in_process("c1-m2")


@pytest.fixture
def forwarder(monkeypatch):
    monkeypatch.setenv("EVENT_SINKS", "http://peer-a:8000/, http://peer-b:8000")
    monkeypatch.setattr(tokens, "service_token", lambda module: f"token-of-{module}")
    monkeypatch.setattr(event_forwarder, "RETRY_DELAYS", (0.01, 0.01))
    fw = event_forwarder.Forwarder()
    yield fw
    fw.stop()


def _use(fw, handler):
    fw._client = httpx.Client(transport=httpx.MockTransport(handler))


def test_event_is_posted_to_every_sink_with_the_service_token(forwarder):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["authorization"], request.headers["content-type"]))
        return httpx.Response(202)

    _use(forwarder, handler)
    ev = events.cloudevent("c1-m2", "ApplicationSubmitted", {"applicationId": "a"})
    forwarder.submit(ev)
    assert forwarder.wait_idle()
    assert sorted(seen) == [
        ("http://peer-a:8000/api/v1/events/inbox", "Bearer token-of-c1-m2", "application/cloudevents+json"),
        ("http://peer-b:8000/api/v1/events/inbox", "Bearer token-of-c1-m2", "application/cloudevents+json")]
    assert forwarder.failures == []


def test_transient_errors_are_retried_and_rejections_are_not(forwarder):
    calls = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503 if calls["n"] < 3 else 202)

    _use(forwarder, flaky)
    forwarder._send("http://peer-a:8000", "c1-m2", events.cloudevent("c1-m2", "ApplicationSubmitted"))
    assert calls["n"] == 3 and forwarder.failures == []

    calls["n"] = 0
    _use(forwarder, lambda request: (calls.__setitem__("n", calls["n"] + 1), httpx.Response(400))[1])
    forwarder._send("http://peer-a:8000", "c1-m2", events.cloudevent("c1-m2", "ApplicationSubmitted"))
    assert calls["n"] == 1 and forwarder.failures[0]["error"] == "HTTP 400"


def test_nothing_is_forwarded_without_sinks(monkeypatch):
    monkeypatch.delenv("EVENT_SINKS", raising=False)
    fw = event_forwarder.Forwarder()
    fw.submit(events.cloudevent("c1-m2", "ApplicationSubmitted"))
    assert fw.wait_idle(0.1) and not fw._threads


def test_received_events_are_not_forwarded_again(monkeypatch):
    sent = []
    monkeypatch.setattr(event_forwarder.FORWARDER, "submit", sent.append)
    events.RELAY.receive(events.cloudevent("c1-m2", "ApplicationSubmitted"))
    assert sent == []
    ev = events.publish("c3-m1", "CompanyCreated", {"companyId": "c"})
    assert sent == [ev]


# ---------------------------------------------------------------- event hub (ADR-0006)
def test_without_event_sinks_published_events_go_to_the_hub_by_its_neighbour_address(forwarder, monkeypatch):
    monkeypatch.delenv("EVENT_SINKS")
    monkeypatch.setenv("C12_M1_URL", "http://operations:8000/")
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["authorization"], json.loads(request.content)["id"]))
        return httpx.Response(202)

    _use(forwarder, handler)
    ev = events.cloudevent("c1-m2", "ApplicationSubmitted", {"applicationId": "a"})
    forwarder.submit(ev)
    assert forwarder.wait_idle()
    assert seen == [("http://operations:8000/api/v1/events/inbox", "Bearer token-of-c1-m2", ev["id"])]


def test_hub_and_event_sinks_are_posted_once_each_and_never_to_the_own_runtime(monkeypatch):
    monkeypatch.setenv("MODULE_URLS", '{"process_orchestration": "http://operations:8000"}')
    monkeypatch.setenv("EVENT_SINKS", f"http://operations:8000, {BASE}, http://security:8000")
    assert event_forwarder.targets() == ["http://operations:8000", "http://security:8000"]
    monkeypatch.setenv("C12_M1_URL", "in-process")   # the hub's own runtime, or the monolith
    monkeypatch.delenv("EVENT_SINKS")
    assert event_forwarder.targets() == []


def test_an_event_that_comes_back_to_its_publishing_runtime_is_delivered_once(monkeypatch):
    monkeypatch.setattr(event_forwarder.FORWARDER, "submit", lambda ev: None)
    ev = events.publish("c3-m1", "CompanyCreated", {"companyId": "c"})
    assert events.RELAY.receive(dict(ev)) == (ev, False)   # e.g. routed back by a misconfigured hub: no loop
    assert [e["id"] for e in events.RELAY.log].count(ev["id"]) == 1


def _split(monkeypatch, urls: dict) -> None:
    monkeypatch.setenv("MODULE_URLS_DEFAULT", "")    # modules not named: built-in stand-ins
    monkeypatch.setenv("MODULE_URLS", json.dumps(urls))
    for name in ("C11_M1_URL", "C12_M1_URL"):
        monkeypatch.setenv(name, "in-process")       # the runtime `operations` serves both


def test_hub_routes_to_subscriber_runtimes_but_not_back_to_the_publisher_or_locally(monkeypatch):
    _split(monkeypatch, {"registration": "http://onboarding:8000", "technical_user": "http://security:8000",
                         "credentials": "http://security:8000"})
    submitted = events.cloudevent("c1-m2", "ApplicationSubmitted", {"applicationId": "a"})
    assert event_hub.destinations(submitted) == ["http://security:8000"]   # C2-M3; C11-M1 is local
    issued = events.cloudevent("c4-m1", "CredentialsIssued", {"companyId": "c"})
    assert event_hub.destinations(issued) == []   # C2-M3 runs with the publisher C4-M1: already delivered there
    monkeypatch.setenv("C2_M3_URL", "")   # stand-in: nothing to deliver
    assert event_hub.destinations(submitted) == []


def test_in_the_monolith_the_hub_routes_nothing(monkeypatch):
    sent = []
    monkeypatch.setattr(event_forwarder.FORWARDER, "dispatch", lambda ev, to: sent.append(to))
    assert event_hub.route(events.cloudevent("c1-m2", "ApplicationSubmitted", {"applicationId": "a"})) == []
    assert sent == []   # every subscriber is in-process: the relay delivers, nothing leaves the process


def test_the_hub_runs_its_flows_on_inbox_events_and_routes_them_on_once(monkeypatch):
    """Runtime `operations` (ADR-0005) as the hub: an event of the onboarding runtime arrives at the inbox,
    starts the onboarding flow and goes on to the runtime of C2-M3; a repeated delivery goes nowhere."""
    from runtimes import operations

    _split(monkeypatch, {"technical_user": "http://security:8000"})
    routed: list[tuple[str, str, list[str]]] = []
    monkeypatch.setattr(event_forwarder.FORWARDER, "dispatch",
                        lambda ev, to: routed.append((ev["type"], ev["id"], to)) if to else None)
    application = "0f8e2d4c-6b1a-4c3e-8f7d-2a9b1c0d3e4f"   # FRAMEWORK 7a
    ev = events.cloudevent("c1-m2", "ApplicationSubmitted", {
        "applicationId": application, "companyId": "c0000001-0000-4000-8000-000000000001", "kind": "ONBOARDING",
        "existingCompany": False, "applicantSub": "5a1c0001-0000-4000-8000-000000000001"})
    with TestClient(operations.create_app(), base_url=BASE) as client:   # relay and worker run
        headers = bearer(tokens.service_token("c1-m2")) | {"Content-Type": "application/cloudevents+json"}
        for _ in range(2):
            assert client.post("/api/v1/events/inbox", headers=headers, content=json.dumps(ev)).status_code == 202
        assert events.RELAY.wait_idle(10)
        started = [e for e in events.RELAY.log if e["type"] == "ProcessStarted"]
    assert [(e["data"]["flowKey"], e["data"]["subjectId"]) for e in started] == [("onboarding", application)]
    assert [r for r in routed if r[1] == ev["id"]] == [("ApplicationSubmitted", ev["id"], ["http://security:8000"])]
    assert ("ProcessStarted", started[0]["id"], ["http://security:8000"]) in routed   # the hub's own events too

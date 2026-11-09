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

import os

import httpx
import pytest
from conftest import BASE
from fastapi.testclient import TestClient

from features import company_profile, registration
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
    assert layout.features() == {"c1-m2": "registration", "c3-m1": "company_profile"}
    assert (registration.NAME, registration.MODULE) == ("registration", "c1-m2")
    assert (company_profile.NAME, company_profile.MODULE) == ("company_profile", "c3-m1")
    assert layout.interface_package("c3-m1") == "features.company_profile.interface"
    assert layout.interface_package("c12-m1") == "modules.c12_m1.interface"   # not migrated yet


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
    assert any(p.startswith("/api/c1-m2/") for p in paths) and not any(p.startswith("/api/c3-m1/") for p in paths)


def test_runtime_mixes_features_and_modules_not_migrated_yet():
    assert [e["module"] for e in _served(create_runtime(company_profile, "process_orchestration"))] == ["c3-m1", "c12-m1"]


def test_runtime_name_selects_a_runtime_or_a_feature():
    assert runtime_main.factory("onboarding") == "runtimes.onboarding:create_app"
    assert runtime_main.factory("installation") == "runtimes.installation:create_app"
    assert runtime_main.factory("company-profile") == "features.company_profile.main:create_app"
    with pytest.raises(SystemExit, match="unknown runtime"):
        runtime_main.factory("onboardng")


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

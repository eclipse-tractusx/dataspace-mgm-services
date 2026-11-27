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
#  Assisted-By: GitHub Copilot
#################################################################################
"""HTTP tests of App Access (C2-M2) under /api/app-access: the controller tree against the spec, tokens, scope,
validation and Problem Details, inside the installation and as its own runtime."""
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from c2_m2_database import _empty_c2_m2_database  # noqa: F401 - autouse: empty tables with a database
from conftest import BASE, bearer, needs_admin_api, person_token
from features.app_access import interface
from features.app_access.main import create_app as standalone_app
from features.app_access.router import router as feature_router
from portal_common import http, layout, spec, tokens
from scaffold.app import create_app, reset_all

API = "/api/app-access"
COMPANY = "c0000001-0000-4000-8000-000000000001"
USER = "5a1c0001-0000-4000-8000-000000000001"

def operations(document):
    return {
        (path, method): item[method]
        for path, item in document["paths"].items()
        for method in spec.METHODS if method in item
    }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("C3_M1_URL", "")
    monkeypatch.setenv("C10_M1_URL", "")
    app = create_app()
    http.register_local(BASE, app)
    yield TestClient(app, base_url=BASE)
    reset_all(app.state.entries)


def test_base_path_is_the_readable_feature_name():
    assert layout.base_path("c2-m2") == API


def test_every_operation_of_the_spec_is_routed_once_with_its_operation_id():
    expected = operations(spec.module("c2-m2").document)
    routes = [route for route in feature_router.routes if isinstance(route, APIRoute)]
    actual = {(route.path.removeprefix(API), method.lower()): route for route in routes for method in route.methods}
    assert len(routes) == len(expected) == 36
    assert actual.keys() == expected.keys()
    for key, route in actual.items():
        assert route.operation_id == expected[key]["operationId"]
        assert route.include_in_schema is True
        assert route.tags[0].startswith("App Access: ")
    assert {route.status_code for route in routes if "delete" in {m.lower() for m in route.methods}} == {204}


@pytest.mark.parametrize("private", [False, True])
def test_every_http_endpoint_requires_authentication(client, private):
    for (path, method), operation in operations(spec.module("c2-m2").document).items():
        if path.startswith(("/internal/", "/steps/")) != private:
            continue
        for name in ("companyId", "userId", "appId", "invitationId", "id"):
            path = path.replace("{" + name + "}", COMPANY if name == "companyId" else USER)
        response = client.request(method.upper(), API + path, json={})
        assert response.status_code == 401, operation["operationId"]
        assert response.headers["content-type"] == "application/problem+json"
        assert response.json()["type"] == "urn:c2-m2:problem:unauthorized"
        if path.startswith("/steps/"):
            assert "retryable" in response.json()


def test_the_old_spec_path_answers_404(client):
    response = client.get("/api/c2-m2/osp/users", headers=bearer(person_token("max")))
    assert response.status_code == 404


def test_private_queries_still_work_with_service_tokens_and_reject_people(client):
    response = client.get(API + "/internal/company-users", params={"companyId": COMPANY},
                          headers=bearer(person_token("otto")))
    assert response.status_code == 403
    response = client.get(API + "/internal/company-users", params={"companyId": COMPANY},
                          headers=bearer(tokens.service_token("c11-m1")))
    assert response.status_code == 200
    assert response.json() == []
    response = client.get(API + "/internal/company-users", params={"companyId": "not-a-uuid"},
                          headers=bearer(tokens.service_token("c11-m1")))
    assert response.status_code == 400
    assert response.json()["type"] == "urn:c2-m2:problem:validation"


def test_public_handlers_preserve_scope_validation_and_camel_case(client):
    interface.assign_company_admin({
        "processId": COMPANY, "stepRunId": USER,
        "companyId": COMPANY, "bpn": "BPNLIUK2REMLK3F4", "applicantSub": USER,
    })
    headers = bearer(person_token("erika"))
    response = client.get(API + f"/companies/{COMPANY}/users", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"][0]["userId"] == USER
    assert response.json()["items"][0]["portalRoles"] == ["Company Admin"]
    response = client.get(API + "/companies/c0000002-0000-4000-8000-000000000002/users", headers=headers)
    assert response.status_code == 404
    response = client.post(API + f"/companies/{COMPANY}/invitations", headers=headers,
                           json={"givenName": "Max", "familyName": "Mustermann", "portalRoles": ["Member"]})
    assert response.status_code == 201
    assert len(response.json()["code"]) == 43
    response = client.post(API + f"/companies/{COMPANY}/invitations", headers=headers, json=[])
    assert response.status_code == 400
    assert response.json()["type"] == "urn:c2-m2:problem:validation"


def test_service_errors_leave_as_problem_details_of_the_module(client):
    """A service error (not a Problem) is translated by `translated`, not turned into 500."""
    interface.assign_company_admin({
        "processId": COMPANY, "stepRunId": USER,
        "companyId": COMPANY, "bpn": "BPNLIUK2REMLK3F4", "applicantSub": USER,
    })
    response = client.get(API + f"/companies/{COMPANY}/users", params={"status": "BOGUS"},
                          headers=bearer(person_token("erika")))
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["type"] == "urn:c2-m2:problem:validation"


def test_scaffold_preserves_complete_api_without_fallback_duplicates(client):
    document = client.get("/openapi.json").json()
    paths = {path for path in document["paths"] if path.startswith(API + "/")}
    assert paths == {API + path for path in spec.module("c2-m2").document["paths"]}
    for path in paths:
        for method in spec.METHODS:
            if method in document["paths"][path]:
                assert "stand-in" not in document["paths"][path][method].get("summary", "")


@needs_admin_api
def test_delete_answers_204_without_body(client):
    interface.assign_company_admin({
        "processId": COMPANY, "stepRunId": USER,
        "companyId": COMPANY, "bpn": "BPNLIUK2REMLK3F4", "applicantSub": USER,
    })
    headers = bearer(person_token("erika"))
    created = client.post(API + f"/companies/{COMPANY}/invitations", headers=headers,
                          json={"givenName": "Max", "familyName": "Mustermann", "portalRoles": ["Member"]}).json()
    response = client.delete(API + f"/companies/{COMPANY}/invitations/{created['id']}", headers=headers)
    assert response.status_code == 204
    assert response.content == b""


def test_own_runtime_serves_the_whole_api_and_checks_tokens(monkeypatch):
    monkeypatch.setenv("C2_M2_URL", "in-process")   # create_runtime sets it; monkeypatch restores it
    app = standalone_app()
    client = TestClient(app, base_url=BASE)   # without `with`: no lifespan, so no database is needed
    assert client.get("/health").json()["status"] == "UP"
    paths = {path for path in client.get("/openapi.json").json()["paths"] if path.startswith(API + "/")}
    assert paths == {API + path for path in spec.module("c2-m2").document["paths"]}
    response = client.get(API + "/osp/users")
    assert (response.status_code, response.json()["type"]) == (401, "urn:c2-m2:problem:unauthorized")
    response = client.get(API + "/osp/users", headers=bearer(person_token("max")))
    assert (response.status_code, response.json()["type"]) == (403, "urn:c2-m2:problem:forbidden")
    response = client.get(API + "/no-such-path")
    assert response.headers["content-type"] == "application/problem+json"

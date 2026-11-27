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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from features.dataspace_issuer_interface.main import create_app
from portal_common import http as portal_http
from portal_common import neighbours

CLIENT = TestClient(create_app())


def response(method: str, url: str, status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request(method, url))


def test_health_is_public():
    result = CLIENT.get("/api/dataspace-issuer-interface/health")

    assert result.status_code == 200
    assert result.json() == {"status": "ok", "service": "dataspace-issuer-interface"}


def test_holder_registration_is_open_and_calls_issuer_admin_api(monkeypatch):
    calls: list[tuple[str, str, dict, dict]] = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["json"], kwargs["headers"]))
        return response(method, url, 204)

    monkeypatch.setenv("ISSUER_SERVICE_ADMIN_URL", "https://issuer.example/api/admin")
    monkeypatch.setenv("ISSUER_SERVICE_API_KEY", "issuer-test-key")
    monkeypatch.setattr(portal_http, "request", fake_request)

    result = CLIENT.post(
        "/api/dataspace-issuer-interface/holders",
        json={"holderId": "BPN1", "did": "did:web:wallet", "memberOf": "Catena-X"},
    )

    assert result.status_code == 204
    assert calls[0][0:2] == ("POST", "https://issuer.example/api/admin/v1beta/participants/issuer/holders")
    assert calls[0][2] == {
        "holderId": "BPN1",
        "did": "did:web:wallet",
        "properties": {"memberOf": "Catena-X"},
    }


def test_credential_request_calls_wallet_identity_api(monkeypatch):
    calls: list[tuple[str, str, dict, dict]] = []
    wallet_queries: list[tuple[str, str, str, dict]] = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["json"], kwargs["headers"]))
        return response(method, url, 202)

    def fake_wallet_query(caller, target, function, **params):
        wallet_queries.append((caller, target, function, params))
        return {
            "issuanceMode": "HOLDER_REQUESTS",
            "identityApiUrl": "https://wallet.example/api/identity",
            "participantContextId": "wallet-context",
            "apiKey": "wallet-test-key",
        }

    monkeypatch.setattr(portal_http, "request", fake_request)
    monkeypatch.setattr(neighbours, "query", fake_wallet_query)

    result = CLIENT.post(
        "/api/dataspace-issuer-interface/credentials/request",
        json={
            "company_id": "company-1",
            "issuer_did": "did:web:issuer.example",
            "holder_pid": "company:BPN:1",
            "credential_definition": "bpn-credential-definition",
            "credential_format": "VC1_0_JWT",
        },
    )

    assert result.status_code == 202
    assert result.json() == {"holderPid": "company:BPN:1"}
    assert wallet_queries == [("c4-m1", "c4-m2", "get_holder_access", {"companyId": "company-1"})]
    assert calls[0][0:2] == (
        "POST",
        "https://wallet.example/api/identity/v1beta/participants/wallet-context/credentials/request",
    )


def test_credential_request_can_target_another_identityhub_with_its_own_version(monkeypatch):
    calls: list[str] = []

    def fake_request(method, url, **kwargs):
        calls.append(url)
        return response(method, url, 202)

    monkeypatch.setattr(
        neighbours,
        "query",
        lambda *_args, **_kwargs: {
            "issuanceMode": "HOLDER_REQUESTS",
            "identityApiUrl": "https://second-wallet.example/api/identity",
            "participantContextId": "second-wallet-context",
            "apiKey": "second-wallet-test-key",
        },
    )
    monkeypatch.setenv("ISSUER_SERVICE_API_VERSION", "v1beta")
    monkeypatch.setattr(portal_http, "request", fake_request)

    result = CLIENT.post(
        "/api/dataspace-issuer-interface/credentials/request",
        json={
            "company_id": "company-2",
            "identity_api_version": "v2alpha",
            "issuer_did": "did:web:issuer.example",
            "holder_pid": "company:BPN:2",
            "credential_definition": "membership-credential-definition",
            "credential_format": "VC1_0_JWT",
        },
    )

    assert result.status_code == 202
    assert calls == [
        "https://second-wallet.example/api/identity/v2alpha/participants/second-wallet-context/credentials/request"
    ]

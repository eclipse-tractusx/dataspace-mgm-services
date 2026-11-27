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

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import httpx

from features.dataspace_issuer_interface.interface import (
    HolderRegistration,
    get_holder,
    get_holders,
    register_holder,
)
from features.dataspace_issuer_interface.managers.identity_service_http_client import IdentityServiceHttpClient
from features.dataspace_issuer_interface.models.wallet_credential_request import WalletCredentialRequest
from portal_common import http as portal_http


def response(method: str, url: str, status: int = 204) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request(method, url))


def test_register_holder_uses_issuer_admin_api(monkeypatch):
    calls: list[tuple[str, str, dict, dict]] = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["json"], kwargs["headers"]))
        return response(method, url)

    monkeypatch.setenv("ISSUER_SERVICE_ADMIN_URL", "https://issuer.example/api/admin")
    monkeypatch.setenv("ISSUER_SERVICE_PARTICIPANT_ID", "issuer")
    monkeypatch.setenv("ISSUER_SERVICE_API_KEY", "secret")
    monkeypatch.setattr(portal_http, "request", fake_request)

    register_holder(HolderRegistration(holderId="BPN123", did="did:web:wallet.example", memberOf="Catena-X"))

    assert calls == [(
        "POST",
        "https://issuer.example/api/admin/v1beta/participants/issuer/holders",
        {"holderId": "BPN123", "did": "did:web:wallet.example", "properties": {"memberOf": "Catena-X"}},
        {"x-api-key": "secret"},
    )]


def test_get_holders_queries_issuer_admin_api(monkeypatch):
    calls: list[tuple[str, str, dict, dict]] = []
    holders = [{"holderId": "BPN123", "did": "did:web:wallet.example"}]

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["json"], kwargs["headers"]))
        return httpx.Response(200, json=holders, request=httpx.Request(method, url))

    monkeypatch.setenv("ISSUER_SERVICE_ADMIN_URL", "https://issuer.example/api/admin")
    monkeypatch.setenv("ISSUER_SERVICE_PARTICIPANT_ID", "issuer")
    monkeypatch.setenv("ISSUER_SERVICE_API_KEY", "secret")
    monkeypatch.setattr(portal_http, "request", fake_request)

    result = get_holders()

    assert result == holders
    assert calls == [(
        "POST",
        "https://issuer.example/api/admin/v1beta/participants/issuer/holders/query",
        {},
        {"x-api-key": "secret"},
    )]


def test_get_holder_uses_issuer_admin_api(monkeypatch):
    calls: list[tuple[str, str, dict]] = []
    holder = {"holderId": "BPN123", "did": "did:web:wallet.example"}

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return httpx.Response(200, json=holder, request=httpx.Request(method, url))

    monkeypatch.setenv("ISSUER_SERVICE_ADMIN_URL", "https://issuer.example/api/admin")
    monkeypatch.setenv("ISSUER_SERVICE_PARTICIPANT_ID", "issuer")
    monkeypatch.setenv("ISSUER_SERVICE_API_KEY", "secret")
    monkeypatch.setattr(portal_http, "request", fake_request)

    result = get_holder("BPN123")

    assert result == holder
    assert calls[0][0:2] == (
        "GET",
        "https://issuer.example/api/admin/v1beta/participants/issuer/holders/BPN123",
    )
    assert calls[0][2]["headers"] == {"x-api-key": "secret"}
    assert "json" not in calls[0][2]


def test_request_credential_starts_at_wallet_and_does_not_call_issuer(monkeypatch):
    calls: list[tuple[str, str, dict, dict]] = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["json"], kwargs["headers"]))
        return response(method, url, status=202)

    monkeypatch.setattr(portal_http, "request", fake_request)

    holder_pid = "company:BPN:1"
    client = IdentityServiceHttpClient()
    result = client.request_credential(WalletCredentialRequest(
        identity_api_url="https://wallet.example/api/identity",
        participant_context_id="company-context",
        api_key="wallet-secret",
        issuer_did="did:web:issuer.example",
        holder_pid=holder_pid,
        credential_definition="bpn-credential-definition",
        credential_format="VC1_0_JWT",
    ))

    assert result == holder_pid
    assert calls == [(
        "POST",
        "https://wallet.example/api/identity/v1beta/participants/company-context/credentials/request",
        {
            "issuerDid": "did:web:issuer.example",
            "holderPid": holder_pid,
            "credentials": [{
                "id": "bpn-credential-definition",
                "type": "bpn-credential-definition",
                "format": "VC1_0_JWT",
            }],
        },
        {"x-api-key": "wallet-secret"},
    )]


def test_parallel_wallet_requests_keep_request_data_isolated(monkeypatch):
    request_count = 8
    all_requests_started = Barrier(request_count)
    calls: dict[str, tuple[str, dict, dict]] = {}
    calls_lock = Lock()

    def fake_request(method, url, **kwargs):
        all_requests_started.wait(timeout=5)
        holder_pid = kwargs["json"]["holderPid"]
        with calls_lock:
            calls[holder_pid] = (url, kwargs["headers"], kwargs["json"])
        return response(method, url, status=202)

    monkeypatch.setattr(portal_http, "request", fake_request)
    client = IdentityServiceHttpClient()
    requests = [
        WalletCredentialRequest(
            identity_api_url=f"https://wallet-{index}.example/api/identity",
            participant_context_id=f"wallet-context-{index}",
            api_key=f"wallet-key-{index}",
            issuer_did="did:web:issuer.example",
            holder_pid=f"company:BPN:{index}",
            credential_definition=f"credential-definition-{index}",
            credential_format="VC1_0_JWT",
        )
        for index in range(request_count)
    ]

    with ThreadPoolExecutor(max_workers=request_count) as executor:
        results = list(executor.map(client.request_credential, requests))

    assert results == [request.holder_pid for request in requests]
    assert len(calls) == request_count
    for index, request in enumerate(requests):
        url, request_headers, body = calls[request.holder_pid]
        assert url == (
            f"https://wallet-{index}.example/api/identity/v1beta/participants/"
            f"wallet-context-{index}/credentials/request"
        )
        assert request_headers == {"x-api-key": f"wallet-key-{index}"}
        assert body["holderPid"] == request.holder_pid
        assert body["credentials"][0]["id"] == f"credential-definition-{index}"


def wallet_request(identity_api_url: str) -> WalletCredentialRequest:
    return WalletCredentialRequest(
        identity_api_url=identity_api_url,
        participant_context_id="ctx",
        api_key="wallet-secret",
        issuer_did="did:web:issuer.example",
        holder_pid="p1",
        credential_definition="def-1",
        credential_type="MembershipCredential",
        credential_format="VC1_0_JWT",
    )


def test_wallet_url_is_not_versioned_twice(monkeypatch):
    urls: list[str] = []
    monkeypatch.setattr(portal_http, "request", lambda m, u, **kw: urls.append(u) or response(m, u, status=201))

    IdentityServiceHttpClient().request_credential(wallet_request("https://wallet.example/api/identity/v1beta"))

    assert urls == ["https://wallet.example/api/identity/v1beta/participants/ctx/credentials/request"]


def test_api_version_is_configurable_and_type_is_kept(monkeypatch):
    calls: list[tuple[str, dict]] = []

    def fake_request(method, url, **kwargs):
        calls.append((url, kwargs["json"]))
        return response(method, url, status=201)

    monkeypatch.setenv("ISSUER_SERVICE_API_VERSION", "v1")
    monkeypatch.setenv("ISSUER_SERVICE_ADMIN_URL", "https://issuer.example/api/admin")
    monkeypatch.setattr(portal_http, "request", fake_request)

    IdentityServiceHttpClient().request_credential(wallet_request("https://wallet.example/api/identity"))
    register_holder(HolderRegistration(holderId="BPN1", did="did:web:w"))

    assert calls[0][0] == "https://wallet.example/api/identity/v1/participants/ctx/credentials/request"
    assert calls[0][1]["credentials"] == [
        {"id": "def-1", "type": "MembershipCredential", "format": "VC1_0_JWT"}]
    assert calls[1][0] == "https://issuer.example/api/admin/v1/participants/issuer/holders"

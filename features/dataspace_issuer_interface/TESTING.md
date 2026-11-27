<!--
 Copyright (c) 2026 Contributors to the Eclipse Foundation

 See the NOTICE file(s) distributed with this work for additional
 information regarding copyright ownership.

 This program and the accompanying materials are made available under the
 terms of the Apache License, Version 2.0 which is available at
 https://www.apache.org/licenses/LICENSE-2.0.

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

 AI Disclosure: This file was entirely AI-generated.
 The AI-generated portions are made available under CC0-1.0 and not subject
 to the project's license. The human contributor has reviewed and verified
 that the code is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: GitHub Copilot (GPT-5.1)
-->

# Testing the Dataspace Issuer Interface

The feature is a stateless outbound issuer caller. Its tests verify HTTP request construction and failure handling; they do not run a DCP issuer. DCP starts only after the holder wallet receives the wallet-side request and sends its protocol message to IssuerService.

## Fast local checks

From the repository root:

```bash
uv run ruff check features/dataspace_issuer_interface
uv run pytest -q tests/test_dataspace_issuer_interface.py
uv run pytest -q tests/test_dataspace_issuer_interface_http.py
uv run uvicorn --factory features.dataspace_issuer_interface.main:create_app --port 8000
```

The tests replace `portal_common.http.request` and `portal_common.neighbours.query` with fakes. No live network, wallet, or IssuerService is needed.

The standalone API exposes:

- `GET /api/dataspace-issuer-interface/health`;
- `POST /api/dataspace-issuer-interface/holders`; and
- `POST /api/dataspace-issuer-interface/credentials/request`.

The holder and credential-request endpoints are currently unauthenticated.

## What the tests verify

### Holder registration

`DataspaceIssuerInterface.register_holder()` sends:

```http
POST {ISSUER_SERVICE_ADMIN_URL}/{apiVersion}/participants/{participantId}/holders
x-api-key: {ISSUER_SERVICE_API_KEY}
```

When `ISSUER_SERVICE_ADMIN_URL` is the admin base (for example,
`https://issuer.example/api/admin`), `apiVersion` defaults to `v1beta` and
`participantId` defaults to `issuer`. If the configured URL already contains
`/participants/`, it is used as the participant-admin base unchanged.

The JSON body contains the holder BPN, wallet DID, and optional `memberOf` property. A `409 Conflict` is treated as idempotent success because the holder may already exist.

The HTTP endpoint is:

```http
POST /api/dataspace-issuer-interface/holders
```

### Wallet-first issuance

`IdentityCaller.request_credential()` queries C4-M2 `get_holder_access` with
the company ID, then sends the request to the wallet details returned by C4-M2.
The public request body contains company and credential identifiers only:

```json
{
  "company_id": "c0000001-0000-4000-8000-000000000001",
  "issuer_did": "did:web:issuer.example",
  "holder_pid": "company:BPN:1",
  "credential_definition": "bpn-credential-definition",
  "credential_type": "BpnCredential",
  "credential_format": "VC1_0_JWT"
}
```

The feature never accepts the wallet URL, participant context, or API key from
the public caller. C4-M2 returns those details; the feature then calls the
wallet Identity API. The wallet performs the DCP exchange after accepting this
request.

The onboarding request supplies `company_id`, `issuer_did`, `holder_pid`,
`credential_definition`, `credential_format`, and optional `credential_type`
and `identity_api_version`. C4-M2 supplies the selected wallet's Identity API
URL, participant context, and API key. `C4_M2_URL` or `MODULE_URLS` configures
the neighbor when it is not in-process. The neighbor call uses the `svc-c4-m1`
service identity, which must be configured for a split runtime.

The HTTP endpoint is:

```http
POST /api/dataspace-issuer-interface/credentials/request
```

## Configuration used by the issuer caller

Values are read when an operation is called:

```bash
export ISSUER_SERVICE_ADMIN_URL=https://issuer.example/api/admin
export ISSUER_SERVICE_PARTICIPANT_ID=issuer
export ISSUER_SERVICE_API_KEY=replace-with-a-test-secret
```

Never commit or print real values for `ISSUER_SERVICE_API_KEY` or wallet API keys. The local unit tests use fake values only.

## Optional integration test

A real integration test requires all of the following:

- a running Tractus-X IssuerService with its Admin API enabled;
- an IssuerService participant context and credential definition;
- a registered WalletA participant context with a resolvable DID;
- a wallet Identity API reachable from the management service;
- C4-M2 reachable in-process or by `C4_M2_URL` / `MODULE_URLS`, with the
  `svc-c4-m1` service account authorized for `get_holder_access`, Portal IAM
  reachable, and production `SERVICE_CLIENT_SECRET` configured;
- a test-only API key for the IssuerService Admin API; and
- a test credential definition and issuer DID.

Run the caller from a controlled test process with the test environment configured, then verify:

1. the holder exists in the IssuerService participant context;
2. the wallet request is accepted;
3. WalletA sends the DCP `CredentialRequestMessage` to IssuerService;
4. the VC is delivered and stored by WalletA; and
5. no API key or client secret appears in logs or response details.

Do not use production wallets, issuer keys, or credentials for this test. The issuer caller currently does not implement IssuerService revocation because the current revocation API requires an issuer credential ID that this feature does not retain.

## Failure cases

The HTTP client maps these responses without including response bodies or secrets in error messages:

- connection errors and timeouts: retryable;
- `408`, `429`, and `5xx`: retryable;
- other `4xx`: non-retryable;
- `409` during holder registration: success.

These error-mapping branches are documented behavior but are not currently
covered by the focused tests.

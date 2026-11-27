<!--
 Copyright (c) 2026 Catena-X Automotive Network e.V.
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

# Dataspace Issuer Interface (module id not assigned)

This is an outbound issuer-caller implementation. It is not migrated from
`modules/<id>/`, and no backend specification module has been assigned to it
yet. It exposes a standalone HTTP API for trusted internal callers and an
in-process interface; C4-M1 remains the owner of portal credential state.

## What it does

The feature provides a stateless HTTP adapter between onboarding callers, C4-M2,
IdentityHub, and the IssuerService. It keeps external URLs, authentication
headers, payloads and response parsing out of credential lifecycle logic.

The current functionality is:

- register a holder for a company using its BPN and wallet DID;
- start a wallet-side credential request using a configured credential
  definition; and
- translate connection failures and non-successful upstream responses into
  feature-specific errors with retryability information.

It does not implement revocation or replace the portal's shared Problem
Details route.

The primary caller is the Credentials feature (C4-M1). It owns credential
issuance state and business decisions; this feature only performs the remote
IssuerService interaction and returns a normalized result. The Dataspace
Wallet Interface (C4-M2) remains responsible for wallet and holder access.

## How it works

### Request flow

1. A caller supplies the company ID and credential request details.
2. `IdentityCaller` queries C4-M2 `get_holder_access` for that company's
  wallet connection details.
3. C4-M2 returns the selected wallet's Identity API URL, participant context,
  and API key. `portal_common.neighbours` handles in-process calls or HTTP
  with the `svc-c4-m1` service token.
4. `IdentityServiceHttpClient` sends the credential request to that wallet's
  IdentityHub. IdentityHub starts the DCP exchange with IssuerService.
5. A successful response means IdentityHub accepted the request; it does not
  confirm that the VC was issued. C4-M1 owns the credential lifecycle and
  completion tracking.

The adapter does not store credentials, access tokens, API keys or request
secrets. It does not decide when a company may receive a credential and it
does not publish credential lifecycle events. C4-M1 remains responsible for
those decisions and events.

### Operations

The public in-process interface in `interface.py` provides:

| Operation | Purpose |
|---|---|
| `register_holder(request)` | Ensure that the IssuerService knows the holder identified by the company BPN and wallet DID. |
| `get_holders()` / `get_holder(holder_id)` | Read holder metadata from the IssuerService Admin API in-process. |

`IdentityCaller.request_credential(request)` is the issuance service operation.
It does not call an IssuerService issuance endpoint directly. It gets HolderAccess
from C4-M2 and calls the company's wallet, which starts DCP with IssuerService.

The onboarding caller provides `company_id`, `issuer_did`, `holder_pid`,
`credential_definition`, `credential_format`, and optional `credential_type`
and `identity_api_version`. It does not send wallet URLs, participant context,
or wallet API keys. When C4-M2 runs separately, `C4_M2_URL` or `MODULE_URLS`
configures the neighbor. The query uses the `svc-c4-m1` identity and requires
the C4-M2 query permission. `ISSUER_SERVICE_API_VERSION` is also used as the
default IdentityHub API version unless overridden per request.

### Authentication and failures

Inbound endpoints are currently unauthenticated. Outbound calls to the
IssuerService Admin API use `ISSUER_SERVICE_API_KEY`; the IdentityHub API key
is obtained from C4-M2's HolderAccess response. Remote C4-M2 queries use the
shared service-token mechanism. Never log these secrets or request headers.

Transport errors, `408`, `429`, and upstream `5xx` responses are classified as
retryable. Other upstream `4xx` responses are non-retryable. The standalone
application maps retryable `IssuerCallerError` to HTTP `502`, non-retryable
`IssuerCallerError` to `409`, and preserves explicit `InterfaceApiError`
statuses. It does not use the portal's shared Problem Details format.

### Current folder map

| Folder | Responsibility |
|---|---|
| `controllers/` | Declares the holder, credential-request and health endpoints. |
| `services/` | IssuerService holder operations and the C4-M2-to-IdentityHub issuance flow. |
| `managers/` | IssuerService Admin and IdentityHub HTTP clients plus endpoint configuration. |
| `models/` | Pydantic request models for holder registration and credential issuance. |
| `interface.py` | Public in-process operations used by callers and tests. |

The feature has no persistence in its initial scope. IssuerService state and
credential lifecycle state belong to the IssuerService and C4-M1 respectively.

Onboarding flow:

```text
C4-M2 creates or selects the company wallet
  -> POST /holders registers the DID at IssuerService
  -> POST /credentials/request sends company and credential identifiers
  -> IdentityCaller fetches HolderAccess from C4-M2
  -> IdentityServiceHttpClient sends the request to that wallet's Identity API
  -> the wallet starts DCP with IssuerService
```

### Configuration

The feature reads these environment variables at call time:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ISSUER_SERVICE_ADMIN_URL` | Yes, for holder registration | None | IssuerService Admin API base URL. Set it to the admin API base, such as `https://issuer.example/api/admin`, or to the complete participant-admin URL. |
| `ISSUER_SERVICE_API_KEY` | Yes, for holder registration | None | API key sent to IssuerService in the `x-api-key` header. |
| `ISSUER_SERVICE_PARTICIPANT_ID` | No | `issuer` | IssuerService participant context appended to the admin base URL when the full participant-admin URL is not supplied. |
| `ISSUER_SERVICE_API_VERSION` | No | `v1beta` | API version used to construct the IssuerService Admin URL and as the IdentityHub API version fallback. |

The C4-M2 neighbor address is resolved by `portal_common.neighbours` from
`C4_M2_URL` or `MODULE_URLS`. When C4-M2 runs in-process, no URL is required.
For a split deployment, Portal IAM must be reachable and the production
`SERVICE_CLIENT_SECRET` must be configured so `svc-c4-m1` can query HolderAccess.
Holder access is fetched just in time and is not included in the caller's
request, logged, or returned.

The standalone HTTP endpoints are currently unauthenticated.
The IssuerService and wallet API keys above are still used on outbound calls;
they do not authenticate callers to this service. Store those outbound keys in
the deployment's secret store. Do not commit or log them.

### Run and test

Run the standalone API and focused tests with:

```bash
uv run uvicorn --factory features.dataspace_issuer_interface.main:create_app --port 8000
uv run pytest -q tests/test_dataspace_issuer_interface.py
uv run pytest -q tests/test_dataspace_issuer_interface_http.py
```

Endpoints:

- `GET /api/dataspace-issuer-interface/health`
- `POST /api/dataspace-issuer-interface/holders`
- `POST /api/dataspace-issuer-interface/credentials/request`

All three endpoints are currently open without caller authentication.

The focused tests cover:

- holder registration request construction;
- C4-M2 HolderAccess lookup and IdentityHub request construction;
- wallet selection and API-version overrides;
- concurrent wallet requests keeping per-request data isolated; and
- health and public HTTP endpoint behavior.

Timeout and upstream retryability mappings are implemented but are not yet
covered by focused tests.

## Open protocol questions

- Which IssuerService API version and base paths are supported?
- What spec module ID and OpenAPI contract should own this issuer caller?
- Does issuance return synchronously, return a request reference, or require
  a callback/status query?
- Which holder, credential-definition and revocation fields are mandatory?
- Which authentication mechanism is required: API key, OAuth2 client
  credentials, or another mechanism?
- If this becomes an independent feature, should it expose a health check
  through a spec-backed controller?
- Should this remain a manager inside C4-M1 instead of becoming a standalone
  portal feature?

See [KNOWN-KNOWNS.md](KNOWN-KNOWNS.md) for confirmed limitations and integration
risks.

## Related code

- [Credentials feature](../credentials/README.md), which currently contains
  the IssuerService route client and owns credential lifecycle state.
- [Dataspace Wallet Interface](../dataspace_wallet_interface/README.md),
  which owns wallet and holder access.
- [Feature architecture rules](../AGENTS.md).
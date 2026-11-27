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

# Known Knowns

This file records verified behavior, known limitations, and deployment
questions for the standalone Dataspace Issuer Interface. The feature has no
assigned backend spec module yet; the HTTP API is therefore not validated
against a committed OpenAPI contract.

## Confirmed Behavior According to Live Test by AI

- `POST /api/dataspace-issuer-interface/holders` registers holder metadata through the IssuerService Admin API. A `409` response is treated as an already-registered holder and success.
- `POST /api/dataspace-issuer-interface/credentials/request` accepts company and credential identifiers. It does not accept wallet URLs, participant contexts, or wallet API keys.
- `IdentityCaller` obtains wallet access through C4-M2 `get_holder_access`, then `IdentityServiceHttpClient` sends the request to that wallet's Identity API. The wallet initiates DCP.
- The C4-M2 lookup uses `portal_common.neighbours.query("c4-m1", "c4-m2", "get_holder_access", ...)`. A split deployment needs `C4_M2_URL` or a `MODULE_URLS` entry and working Portal IAM service-token configuration for `svc-c4-m1`.
- Wallet issuance is supported only when HolderAccess reports `issuanceMode` as `HOLDER_REQUESTS`; other wallet modes return a conflict.
- `identity_api_version` can override the wallet API version. If omitted, the current code falls back to `ISSUER_SERVICE_API_VERSION`, which also configures the IssuerService Admin API.
- `get_holder()` and `get_holders()` exist on the in-process interface, but do not have standalone HTTP endpoints.
- The feature is stateless. It does not persist VCs, track credential lifecycle state, implement revocation, poll for issuance completion, or receive issuance callbacks. C4-M1 owns portal lifecycle tracking.
- The holder-registration and credential-request HTTP routes are currently unauthenticated by design. IssuerService and wallet API keys are only used on outbound calls.

## Known Risks and Limitations

- **Unauthenticated issuance trigger:** anyone able to reach the standalone API can submit a company ID and credential request. Restrict ingress/network access to trusted onboarding workloads until caller authentication is added.
- **No spec-backed API contract:** route paths, request schemas, permissions, and errors are hand-maintained. There is no module ID or OpenAPI contract for `mount()` validation.
- **Holder registration must be sequenced by the caller:** requesting a credential does not automatically register or verify the holder at IssuerService first.
- **No automatic retry:** transport failures and retryable statuses are classified, but this feature does not retry the operation.
- **Error mapping lacks focused tests:** retryable/non-retryable HTTP mapping and timeout conversion are implemented but are not covered by the current feature tests.
- **Issuance is asynchronous:** HTTP success means the wallet accepted the request, not that a VC was issued. Completion is not reported here.
- **Holder listing may be incomplete:** `get_holders()` sends an empty `QuerySpec` and does not paginate. Completeness depends on the deployed IssuerService query defaults.
- **Version fallback couples two APIs:** `ISSUER_SERVICE_API_VERSION` configures the IssuerService Admin URL and is also used as the IdentityHub API version fallback. A deployment with differing API versions must pass `identity_api_version` on the issuance request.
- **Holder conflict handling is broad:** every `409` during registration is treated as idempotent success; the response is not checked to confirm the existing holder has the requested DID or metadata.
- **Error response contract is provisional:** the standalone app maps `InterfaceApiError` to `{ "detail": ... }`, not the portal's shared Problem Details format.
- **Health is process-only:** `/health` reports that this process is running; it does not probe C4-M2, IdentityHub, or IssuerService.
- **No live integration verification is recorded:** the committed tests mock HTTP calls. They verify request construction, not compatibility with a deployed IdentityHub/IssuerService version.
- **The feature needs a code review:** the whole feature has not been reviewed yet. In particular, `managers/` and `services/` (HTTP clients, configuration, C4-M2 lookup, error translation) still have to be checked for correctness and maintainability.

## Deployment Questions

- The code defaults `ISSUER_SERVICE_API_VERSION` to `v1beta`, while the Admin API version/path may differ by deployment. Confirm the full `ISSUER_SERVICE_ADMIN_URL` and API version against the deployed service.
- The client currently uses `x-api-key` for the IssuerService Admin API. Confirm whether the deployment supports that credential or requires OAuth2.
- In a split deployment, confirm that `svc-c4-m1` exists and has permission to call C4-M2 `get_holder_access`; configure the production `SERVICE_CLIENT_SECRET` rather than the test-only default.
- Confirm the IssuerService query behavior for an empty holder `QuerySpec`, including its default page size and ordering.
- Confirm that C4-M1 remains responsible for completion callbacks, status tracking, and revocation, including how it correlates issued credential IDs when revocation is needed.

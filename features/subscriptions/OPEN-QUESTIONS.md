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
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# C10-M1 open questions

1. **FRAMEWORK 4.1, base path `/api/c10-m1`** "until the common path convention is settled". Implemented: served under the readable feature name `/api/subscriptions` (ADR-0003, decision 2); `/api/c10-m1` answers 404. Problem types, event sources, permissions and the service account `svc-c10-m1` keep the spec id.
2. **Stand-in scope.** The feature is still the stand-in of the module: `end`, `decline`, `instance-url` and the `/internal` queries over HTTP are served by the spec-driven fallback (the queries call `interface.py`). Implementing them is the work of the team that takes over C10-M1.
3. **README 6.1, status before the setup.** The spec starts a subscription with `PENDING`; the stand-in uses `REQUESTED` until the provider starts the setup and `PENDING` afterwards. Kept as it was (`models/subscription.py`, `SubscriptionStatus`), so Process Orchestration and the demo see the same states.
4. **README 7.9, provider configuration.** The spec requires only `tokenUrl` and `clientId` and keeps a stored secret when `clientSecret` is left out. The stand-in requires all five fields and replaces the whole configuration (`ProviderConfigurationInput`). The answer now has the fields of `ProviderConfiguration` (`companyId`, `clientSecretSet`, `updatedAt`).
5. **Responses beside the spec.** `Subscription` of the stand-in has no `setupStarted`, `requestedAt` and the other timestamps of the spec yet; the step result is `{}` instead of `notified` / `called`.

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
 that the content is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# Subscriptions (C10-M1)

Migrated from `modules/c10_m1/` (spec `spec/C10-M1-Subscriptions`).

## What it does

A company subscribes to an active offer (an app or a service of C8-M1 Offers). The feature keeps the subscription
and its status, informs the provider's own system, and lets the provider start the setup and activate the
subscription. The client of the app instance and the technical user that the customer needs are created by other
modules (C2-M2, C2-M3) in the flow `subscription-setup` of Process Orchestration (C12-M1); this feature only
starts and finishes that flow with its events and steps.

Callers:

- people of the subscribing company (UI): subscribe, read their subscription;
- people of the provider company (UI): store the provider configuration, read, start the setup, activate;
- Process Orchestration (C12-M1): the steps `notify-provider` and `send-activation-callback`;
- other modules (C2-M2, C2-M3, C6-M1, C11-M1): the queries `find_subscriptions` and `get_subscription_internal`.

The feature is still the stand-in of the module: it implements the app path of FRAMEWORK 5.8 and leaves the other
operations of `openapi.yaml` (list, end, decline, instance URL, read and delete the provider configuration) to the
spec-driven fallback, which answers 501.

## How it works

Status of a subscription: `REQUESTED` (subscribe) -> `PENDING` (start setup, provider) -> `ACTIVE` (activate,
provider). Activation is refused while the newest `subscription-setup` process at C12-M1 is `RUNNING`
(`setup-not-finished`) or `FAILED` (`setup-failed`). A subscription is visible to its customer and to the provider
company; any other company gets 404, and only the provider may start the setup or activate (403).

| Folder | Content |
|---|---|
| `controllers/subscriptions/` | `POST /subscriptions`, `GET /subscriptions/{offerSubscriptionId}`, `POST .../start-setup`, `POST .../activate` |
| `controllers/provider_configuration/` | `PUT /provider-configuration` |
| `controllers/steps/` | `POST /steps/notify-provider`, `POST /steps/send-activation-callback` |
| `services/subscriptions.py` | subscribe, visibility, start setup, activate, setup status, events |
| `services/provider_configuration.py` | validation and storage of the provider configuration (secret never returned) |
| `services/steps.py` | the two steps: setup notice and activation callback to the provider system |
| `services/queries.py` | the queries of section 9 |
| `managers/subscription_repository.py` | the subscriptions in the feature's database: save, get by id, find by customer, offer and status |
| `managers/provider_configuration_repository.py` | the provider configurations (with secret) in the feature's database |
| `managers/provider_client.py` | client-credentials token at the provider's `tokenUrl`, then POST to `setupUrl` / `callbackUrl` |
| `managers/neighbour_client.py` | queries to C8-M1 (offer), C12-M1 (processes), C3-M1 (customer name), C2-M3 (rotated secret) |
| `models/` | pydantic models on `portal_common.models`: `subscription.py` (spec id, value sets, `SubscriptionRef`, `SubscriptionInternal`, `Subscription`), `requests.py` (`SubscribeRequest`, `StartSetupRequest`, the step inputs `SubscriptionStep` and `ActivationCallbackStep`), `provider_configuration.py` (input, answer without secret, stored form), `tables.py` (SQLModel tables `subscription` and `provider_configuration`), `errors.py` (the Problem factory), `validation.py` (checks interface input against the models: 400 `validation`, as over HTTP) |

In-process interface (`interface.py`, also the entry point of the controllers): the steps `notify_provider(input)` and `send_activation_callback(input)`,
the queries `find_subscriptions(customerCompanyId=, offerId=, status=)` and
`get_subscription_internal(offerSubscriptionId=)`, and the operations of people that the controllers call (`subscribe`, `get_subscription`, `start_setup`, `activate`, `put_provider_configuration`). Steps and queries of the spec without an implementation exist as
stand-in functions (`standin.missing_interface`).

Events published (source `urn:c10-m1`): `SubscriptionRequested`, `SubscriptionSetupStarted`,
`SubscriptionActivated`. The feature consumes no events.

Configuration: neighbours are reached through `portal_common.neighbours` (`C3_M1_URL`, `C8_M1_URL`, `C12_M1_URL`,
`C2_M3_URL` or `MODULE_URLS`); the database through `portal_common.database`.

Persistence: the feature's own database with SQLModel tables (`models/tables.py`), opened only by the repositories in
`managers/`. The URL is `SUBSCRIPTIONS_DATABASE_URL`, then `C10_M1_DATABASE_URL`, then `DATABASE_URL`; without one
the feature runs on a private in-memory SQLite database (tests, `demo.py`). The index creates the tables in
`on_startup()` and `reset()` empties them. The provider secret is stored in plain text; the encryption with
`ENCRYPTION_KEY` of README 4 is not implemented yet.

Run it alone and test it:

```bash
RUNTIME=subscriptions uv run python -m runtimes     # serves /api/subscriptions
uv run pytest -q tests/test_c10_m1_*.py
```

## Links

- [Spec README](../../spec/C10-M1-Subscriptions/README.md) and [openapi.yaml](../../spec/C10-M1-Subscriptions/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

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

# Offers (C8-M1)

Migrated from `modules/c8_m1/` (spec `spec/C8-M1-Offers`).

## What it does

Companies of an installation offer apps and services in a catalogue; OSP staff review an offer before it is
released. This feature is still the stand-in of the hackathon core path: a provider company with the company role
`APP_PROVIDER` or `SERVICE_PROVIDER` creates an offer, sets its planned app roles and its technical user profile and
submits it; OSP staff approve it, which publishes `OfferApproved` and starts the flow `app-approval` of Process
Orchestration. Process Orchestration and C10-M1 Subscriptions read the offer with the lookup `getOfferInternal`.
Every other operation of the spec (marketplace, documents, agreements, decline, deactivate, ...) is answered by the
scaffold fallback with 501.

Callers: people of a provider company (permissions `manage_offers`, `view_offers`, scope `company`), OSP staff
(`approve_offers`), and Process Orchestration and Subscriptions through the query (`query_c8_m1`).

## How it works

States: `DRAFT` -> `IN_REVIEW` (submit; an app needs planned roles) -> `ACTIVE` (approve). A wrong state answers
409 `invalid-state`, an app without roles 409 `incomplete`, an offer of another company 404.

| Folder | Content |
|---|---|
| `controllers/offers/` | `POST /offers`, `GET /offers/{offerId}`, `POST /offers/{offerId}/submit`; scope `company` on the provider of the offer |
| `controllers/offers/roles/` | `PUT /offers/{offerId}/roles` |
| `controllers/offers/technical_user_profile/` | `PUT /offers/{offerId}/technical-user-profile` |
| `controllers/osp/offers/` | `POST /osp/offers/{offerId}/approve` |
| `controllers/internal/offers/` | `GET /internal/offers/{offerId}` (the query over HTTP) |
| `services/offers.py` | the rules: company role of the offer type at C3-M1, the state changes, the event |
| `managers/offer_repository.py` | reads and writes the offers in the feature's database |
| `managers/neighbour_client.py` | C3-M1 `query_company` (in-process or over HTTP, `portal_common.neighbours`) |
| `models/offer.py` | pydantic models: `OfferInput`, `Offer`, `AppRole`, `TechnicalUserProfile`, `OfferInternal`, `OfferEvent`, value sets |
| `models/errors.py` | `MODULE` and the Problem factory (`urn:c8-m1:problem:<name>`) |
| `models/tables.py` | SQLModel table `offer`; roles, profile and agreements are JSON columns of the offer |

- **Interface** (`interface.py`): the query `get_offer_internal(offerId=...)`, the offer as JSON with
  `hasTechnicalUserProfile`, and the operations of people that the controllers call. Every other step or query of the spec is a stand-in function
  (`standin.missing_interface`).
- **Events**: publishes `OfferApproved` (`offerId`, `offerType`, `providerCompanyId`, source `urn:c8-m1`); consumes
  none.
- **Configuration**: no variables of its own. C3-M1 is reached through `C3_M1_URL` or `MODULE_URLS`.
- **Persistence**: its own database through `portal_common.database`: `OFFERS_DATABASE_URL`, then
  `C8_M1_DATABASE_URL`, then `DATABASE_URL`; without one a private in-memory SQLite database. `on_startup()`
  creates the table, `reset()` empties it.
- **Run alone**: `RUNTIME=offers uv run python -m runtimes` (API under `/api/offers`).
- **Test**: `uv run pytest -q tests/test_c8_m1_*.py`.

## Links

- [Spec README](../../spec/C8-M1-Offers/README.md) and [openapi.yaml](../../spec/C8-M1-Offers/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

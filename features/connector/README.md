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
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# Connector (C6-M1)

Migrated from `modules/c6_m1/` (spec `spec/C6-M1-Connector`).

## What it does

The feature keeps the register of the dataspace connectors of the companies of this installation: name, endpoint,
location (country), status, the technical user the connector uses and, for a connector that a provider runs for a
customer, the offer subscription it belongs to. There are two kinds: a company connector (`COMPANY_CONNECTOR`, provider
and host are the same company) and a connector as a service (`CONNECTOR_AS_A_SERVICE`, a provider runs it for the
customer of one of its offers). It does not answer discovery requests: it publishes events, and Process Orchestration
enters the connectors in the discovery of the CSP through C3-M2.

Callers: people of a company in the UI (register, view, change and delete the own connectors, see the connectors a
provider runs for them), people of a provider company (register a connector as a service), Process Orchestration
(the steps of README 8) and C2-M3 Technical Users (the query of README 9.1, before it deletes an account).

## How it works

**Status.** A registered connector is `ACTIVE`. It becomes `INACTIVE` when its subscription ends or is declined
(step 8.1) or when it is deleted while a subscription is linked (the link stays). A connector without a subscription
is removed on delete. Uniqueness (README 5) counts only connectors that are not `INACTIVE`: name with endpoint, the
technical user, the subscription. All changes of the register run under one lock
(`managers/connector_repository.py`), so of two concurrent registrations the second gets 409.

**Folder map.**

| Folder | Contents |
|---|---|
| `controllers/connectors/` | `GET`, `POST /connectors`, `POST /connectors/as-a-service`, `GET`, `PATCH`, `DELETE /connectors/{connectorId}` (README 7, scope `company` from the token) |
| `controllers/steps/` | `POST /steps/deactivate-subscription-connectors`, `POST /steps/unlink-technical-user` (README 8) |
| `controllers/internal/connectors/` | `GET /internal/connectors?technicalUserId=` (README 9.1) |
| `services/connectors.py` | the operations of people with the checks of README 6.2: HTTPS endpoint, country of the reference data, uniqueness, host company `ACTIVE`, technical user usable, subscription of an own offer |
| `services/steps.py`, `services/queries.py` | the two steps and the query |
| `services/common.py` | UUID spelling and the deactivation event |
| `managers/connector_repository.py` | the only code with a database session: the tables of the register, the audit log and the steps' records, and the lock |
| `managers/neighbour_client.py` | C3-M1 `query_company`, C2-M3 `check_technical_user`, C10-M1 `get_subscription_internal`, each with the built-in stand-in of README 11 when the neighbour address is empty |
| `managers/config.py` | the country codes of the reference data (`masterDataFile` of the installation settings) |
| `managers/data/` | `stub-companies.json`, `stub-subscriptions.json`: read-only data of the built-in stand-ins of C3-M1 and C10-M1 |
| `models/connector.py` | pydantic models on `portal_common.models`: `ConnectorInput`, `ConnectorAsAServiceInput`, `EndpointChange`, the step inputs, `Connector`, `ConnectorRef`, `ConnectorIds`, the value sets `ConnectorType`, `ConnectorStatus`, `Role` |
| `models/errors.py` | the Problem Details of C6-M1 (`problem()`) and the check of an in-process dict input against its model (`parse()`) |
| `models/tables.py` | SQLModel tables `connector`, `audit_entry`, `ended_subscription`, `deleted_technical_user` |

**In-process interface** (`interface.py`, call convention of `AGENTS.md`): the steps
`deactivate_subscription_connectors(input)` and `unlink_technical_user(input)`, the query
`list_connectors_internal(technicalUserId=...)`, and the operations of people, which only the controllers call.

**Events** (CloudEvents, `source` `urn:c6-m1`): `ConnectorRegistered`, `ConnectorEndpointChanged`,
`ConnectorDeactivated`, `ConnectorDeleted`. The feature consumes no events.

**Configuration.** The feature reads no environment variable itself. The database URL comes from
`portal_common.database` (`CONNECTOR_DATABASE_URL`, then `C6_M1_DATABASE_URL`, then `DATABASE_URL`). The neighbour addresses `C3_M1_URL`,
`C2_M3_URL`, `C10_M1_URL` (or `MODULE_URLS`) are resolved by `portal_common.neighbours`: empty means the built-in
stand-in, `in-process` the module of this installation. The country list comes from the installation settings.

**Persistence.** The feature's own database through SQLModel (`models/tables.py`): PostgreSQL when a URL is set, else a
private in-memory SQLite database. `on_startup()` creates the tables, `reset()` empties them and reloads the stand-in
data. The uniqueness rules of README 5 are checked under the lock, not by partial unique indexes (OPEN-QUESTIONS.md 12).

**Run and test.**

```bash
RUNTIME=connector uv run python -m runtimes          # the feature alone, API under /api/connector
uv run pytest -q tests/test_c6_m1_connectors.py
```

## Links

- Spec: [README](../../spec/C6-M1-Connector/README.md), [openapi.yaml](../../spec/C6-M1-Connector/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

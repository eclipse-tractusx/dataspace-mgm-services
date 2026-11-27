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

# Technical User (C2-M3)

Migrated from `modules/c2_m3/` (spec `spec/C2-M3-TechnicalUser`).

## What it does

The feature manages the technical users of the companies: one client with a service account per technical user
in the Portal IAM of the onboarding service provider (OSP), signing in with client ID and secret, with roles of
the client `technical_roles_management` and `company_id` and `bpn` in its token. It creates these accounts, shows
them, changes their name, description and roles, rotates their secret and deletes them. If an account needs access
to the company's wallet, it reports that as an event and applies the result of C4-M2 as a step. When a company is
deactivated, its technical users are disabled (not deleted) and enabled again on reactivation.

Callers:

- IT Admin and Company Admin of a company (scope `company`): `/companies/{companyId}/technical-users`;
- OSP staff (scope `osp`): `/osp/technical-users`;
- Process Orchestration: the steps under `/steps` (accounts of a subscription, wallet result, deletion after the
  wallet account, disabling and enabling the accounts of a company or subscription);
- C10-M1 Subscriptions: rotating the secret of a subscription account; C6-M1 Connectors: checking an account;
  C8-M1 Offers: the list of technical user roles (all under `/internal`).

## How it works

### Flows and states

- **Status** (README 6.1): `PENDING` while the client is created or the wallet access is requested, `ACTIVE`,
  `PENDING_DELETION` while the wallet account is removed, `DELETED`; `INACTIVE` is the final status of the account
  of an ended subscription. `disabled` is set while the owner's company is deactivated (6.2).
- **Wallet access**: `NONE`, `REQUESTED` (event `WalletAccessRequested`), `ACTIVE` or `FAILED` (step
  `apply-wallet-access`), `REMOVING` (event `WalletAccessRemovalRequested`, then step `delete`).
- **Creation** (7.2, 8.1): the row is stored `PENDING` with its client ID before the client exists in the Portal
  IAM (6.9); then the client is created or completed, and the row, the logs and the events are saved in one
  transaction. A failed creation removes the row and its own client again.
- **Concurrency** (6.9): work on one company, subscription or account runs under a lock per key (order company,
  subscription, account); a row carries a `version`, and saving a stale row raises a conflict.

### Folder map

| Folder | Content |
|---|---|
| `controllers/companies/technical_users/` | `GET`/`POST /companies/{companyId}/technical-users`, `assignable-roles`, `GET`/`PATCH`/`DELETE /{id}`; `credentials/` serves `POST /{id}/credentials/rotate` |
| `controllers/osp/technical_users/` | `GET /osp/technical-users`, `GET /osp/technical-users/{id}` |
| `controllers/internal/` | `GET /internal/technical-users/{id}`, `POST /internal/technical-users/{id}/credentials/rotate`, `GET /internal/technical-roles` |
| `controllers/steps/` | `POST /steps/<step>` for the six steps of README 8 |
| `services/commands.py`, `queries.py`, `steps.py` | operations of people (7.2, 7.4 to 7.6, 9.2), reading operations (7.1, 7.3, 7.9, 7.10, 9.1), steps (8) |
| `services/state.py`, `accounts.py`, `roles.py` | status rules (6.1, 6.2), shared flows (lookup, visibility 6.3, creation, deletion), assignable roles (6.5) |
| `services/audit.py`, `projections.py`, `iam_access.py`, `process_stub.py` | logs and events (6.8, 10), API shapes, IAM errors (12), stand-in for Process Orchestration (11.3) |
| `managers/technical_user_repository.py` | the only code that opens the database: rows, logs, outbox, client ID sequence, locks per key |
| `managers/iam/` | Portal IAM: Keycloak Admin API (`keycloak.py`) or an in-memory stand-in (`memory.py`) |
| `managers/neighbour_client.py`, `managers/data/stub-companies.json` | C3-M1, C6-M1 and C10-M1, with their built-in stand-ins |
| `managers/config.py` | configuration (below) |
| `models/schemas.py` | request bodies and step inputs (`TechnicalUserCreate`, `TechnicalUserUpdate`, `SubscriptionCredentialsRequest`, `Step*`) on `RequestBody` / `StepRequest` |
| `models/responses.py` | responses and step results (`TechnicalUser`, `TechnicalUserSummary`, `Credentials`, `TechnicalUserCheck`, `AssignableRole`, ...) |
| `models/validation.py` | `parse()`: a failed model check as 400 `validation` with a `detail` (README 12) |
| `models/tables.py`, `models/__init__.py` | SQLModel tables; value sets (`Status`, `WalletAccess`, `Origin`, ...) and the records the services work on |

Request bodies are validated in the services (with `models/validation.py`), not by FastAPI, so the order of the
answers stays as in the spec (for example 404 for an unknown account before 400 for its body) and a 400 has the
`detail` of README 12. Responses are the models of `models/responses.py` (`response_model`); an optional field that
the spec leaves out is left unset and is not in the JSON.

### Interface

`interface.py` (call convention): the steps `create_for_subscription`, `apply_wallet_access`, `delete`,
`disable_company_technical_users`, `enable_company_technical_users`, `disable_subscription_technical_users` take
the step input and return `{stepRunId, state, result}`; the queries `check_technical_user`,
`rotate_subscription_credentials` and `list_technical_roles` take the openapi parameter names; the operations of
people are there too. Every answer is JSON (camelCase), as over HTTP.

### Events

Published: `TechnicalUserCreated`, `TechnicalUserDeleted`, `WalletAccessRequested`, `WalletAccessRemovalRequested`
(source `urn:c2-m3`). They are written to the outbox table in the transaction of the change and published after
it committed; an event that fails for a temporary reason stays in the outbox. Consumed: only the feature's own
wallet events, and only with `PROCESS_STUB=true` (`on_event`).

### Configuration

`managers/config.py`: `WALLET_ROLES`, `PROVIDER_ONLY_ROLES`, `TECHNICAL_USER_CLIENT_ID_PREFIX`,
`ROLE_ASSIGNMENT_FILE`, `PROCESS_STUB`. `managers/iam/`: `IAM_URL` (empty: in-memory IAM) and `IAM_REALM`
(through `portal_common.tokens`),
`C2_M3_CLIENT_ID`, `C2_M3_CLIENT_SECRET`, `TECHNICAL_ROLES_CLIENT`, `COMPANY_ID_ATTRIBUTE`, `BPN_ATTRIBUTE`,
`TECHNICAL_USER_CLIENT_DEFAULT_SCOPES`. Neighbours: `C3_M1_URL`, `C6_M1_URL`, `C10_M1_URL` or `MODULE_URLS`
(empty: built-in stand-in). All are read at call time.

### Persistence

The feature's own database through `portal_common.database`: `TECHNICAL_USER_DATABASE_URL`, then
`C2_M3_DATABASE_URL`, then `DATABASE_URL`; without one, a private in-memory SQLite database. Tables
(`models/tables.py`): `technical_user`, `audit_log`, `role_assignment_log` (README 5), `event_outbox` and
`counter` (the client ID sequence). `on_startup()` creates them, `reset()` empties them. Secrets are never stored.

### Run and test alone

```bash
RUNTIME=technical_user uv run python -m runtimes
uv run pytest -q tests/test_c2_m3_*.py
```

## Links

- [Spec README](../../spec/C2-M3-TechnicalUser/README.md)
- [openapi.yaml](../../spec/C2-M3-TechnicalUser/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

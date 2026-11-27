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

# CSP Connection (C3-M2)

Migrated from `modules/c3_m2/` (spec `spec/C3-M2-CSPConnection`).

## What it does

The CSP Connection is the only place through which an installation uses the core services of the CSP (core
service provider). It registers a company with the CSP, which assigns or confirms its BPN and enters this OSP as the
home OSP; it checks whether a company is already registered at an OSP (duplicate check); it registers and
deregisters the membership in the dataspace, enters the company's DID in the directory BPN -> DID, passes changed
core data to the CSP, transfers a company to this OSP, and enters connectors in the discovery of the CSP.

Callers:

- **Process Orchestration (C12-M1)** runs the steps under `/steps` (register, transfer, update, DID, membership,
  connectors) in its flows.
- **C1-M3 Application Review** calls the duplicate check `GET /internal/find-companies`.
- **OSP staff** (through the UI) read the status of a company at the CSP, `GET /companies/{companyId}`.
- **The CSP** calls back `POST /csp-notifications` with its service account (`OperationCompleted`,
  `CompanyTransferredAway`).

## How it works

**Status of a registration** (spec README 6.1): a company without a row is unknown; `register-company` or
`transfer-company` calls the CSP. A `201` turns the row `REGISTERED` with the BPN, a `202` turns it `PENDING` with the
operation id until the CSP's `OperationCompleted` arrives, a `409` or another business rejection turns it `FAILED`
(a company returning from `TRANSFERRED_AWAY` stays `TRANSFERRED_AWAY`). `CompanyTransferredAway` from the CSP turns a
company `TRANSFERRED_AWAY` and forgets its DID, membership and connectors. Every step is repeatable: a repetition
answers from the stored state without a second call to the CSP and without a second event (FRAMEWORK 4.4). A
completion that arrives before the `202` was stored is kept aside and applied when the step stores the operation
id (OPEN-QUESTIONS 15).

**Folders**

| Folder | Content |
|---|---|
| `controllers/companies/` | `GET /companies/{companyId}`: status at the CSP (OSP staff) |
| `controllers/csp_notifications/` | `POST /csp-notifications`: callbacks of the CSP |
| `controllers/internal/find_companies/` | `GET /internal/find-companies`: duplicate check for C1-M3 |
| `controllers/steps/` | `POST /steps/<step>`: the eight steps of Process Orchestration |
| `services/steps.py` | the steps of README 8: preconditions, repetitions, one call to the CSP, one event |
| `services/registration_state.py` | status changes of README 6.1 and the answer of register/transfer (201, 202, 409, 4xx) |
| `services/notifications.py` | notifications of the CSP, deduplicated by `notificationId` |
| `services/queries.py` | duplicate check (README 9) and the registration view (README 7.1) |
| `services/common.py` | input checks shared by the services and the step answer of FRAMEWORK 4.4 |
| `managers/store.py` | repository of the tables of README 5 (registrations, connectors, notifications, audit, early completions): the only code that opens a database session; one lock for check-then-change |
| `managers/csp_client.py` | calls of the core services API (README 11.1) over HTTP, or the built-in stand-in (11.3), with an audit entry per call |
| `managers/config.py` | `CSP_URL` and `CSP_STUB_FILE`, read at call time |
| `models/schemas.py` | the pydantic models of `components.schemas` in openapi.yaml on the bases of `portal_common.models` (step inputs on `StepRequest`, `StepResult`, `CspRegistration`, `CspCompanyMatch`, `CspNotification`) and the value sets |
| `models/tables.py` | the SQLModel tables of README 5 on `database.table_base(MODULE)` (`csp_registration`, `csp_connector`, `csp_notification`, `audit_entry`, `csp_early_completion`), indexed by the columns the services look up by |
| `models/errors.py` | `MODULE = "c3-m2"` and the Problem Details factories of README 12 |

**In-process interface** (`interface.py`, call convention of the root `AGENTS.md`): the steps `register_company`,
`transfer_company`, `register_did`, `update_company`, `register_membership`, `deregister_membership`,
`register_connector`, `deregister_connector` (plain dict in, `StepReply` out); the query `find_companies`;
`receive_csp_notification`, `get_csp_registration`, `registration_view` and `reset`.

**Events** published with `source` `urn:c3-m2`: `CompanyRegisteredAtCsp`, `CompanyRegistrationAtCspFailed`,
`CompanyDidRegistered`, `CompanyUpdatedAtCsp`, `MembershipRegistered`, `MembershipDeregistered`,
`CompanyTransferredAway`, `ConnectorRegisteredAtCsp`, `ConnectorDeregisteredAtCsp`. The feature consumes no events.

**Configuration**: `CSP_URL` (empty: built-in stand-in) and `CSP_STUB_FILE` (stand-in only) in `managers/config.py`;
`CSP_TOKEN_URL` and `OSP_SIGNING_KEY_FILE` are read by `portal_common.csp`; `ospId`, `ospName` and `ospCompanyFile`
come from the installation settings (`SETTINGS_FILE`). The OSP company of `ospCompanyFile` is seeded as `REGISTERED`.

**Persistence**: SQLModel tables in the feature's own database (`portal_common.database`). The URL is
`CSP_CONNECTION_DATABASE_URL`, then `C3_M2_DATABASE_URL`, then `DATABASE_URL`; without one the feature runs on a
private in-memory SQLite database. `on_startup()` creates the tables and the seed row, `reset()` empties them and
seeds again. The audit table keeps the newest 10,000 entries (OPEN-QUESTIONS 12, 13).

**Run and test**

```bash
RUNTIME=csp_connection uv run python -m runtimes     # API under /api/csp-connection
uv run pytest -q tests/test_c3_m2_*.py
```

## Links

- Spec: [README](../../spec/C3-M2-CSPConnection/README.md), [openapi.yaml](../../spec/C3-M2-CSPConnection/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

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

# Users and App Access (C2-M2)

Migrated from `modules/c2_m2/` (spec `spec/C2-M2-AppAccess`).

## What it does

App Access manages the people in the Portal IAM of the onboarding service provider (OSP) and their access to the
portal and the apps. It binds an account to exactly one company, sets portal roles and app roles, handles
invitations to a company or to the OSP staff, and keeps one client template per app and one instance client per app
instance with their app roles. It never creates an account itself: the Portal IAM creates it at the first login.

Who calls it:

- the UI of the OSP for the Company Admin and the people of a company (scope `company`), for a person without a
  company accepting an invitation (scope `own`) and for the OSP staff (scope `osp`);
- Process Orchestration (C12-M1) with the steps of README section 8: bind the Company Admin during onboarding,
  disable and enable the accounts of a company, create the client template of an approved app, create, enable and
  disable instance clients, change an instance URL, add app roles, update role descriptions;
- other modules with the queries of README section 9: Offers (app roles), Subscriptions (instance clients),
  Notifications (people of a company with a portal role).

## How it works

- **Bindings and roles.** A binding is a row in `company_user` plus the attributes `company_id` and `bpn` on the
  account in the Portal IAM. Portal roles are composite roles on the client `portal-core`; app roles are client
  roles on the instance clients of the active subscriptions of the company (README 6.6 to 6.12).
- **Invitations.** A `COMPANY` or `STAFF` invitation has a random single-use code; only its hash is stored and the
  code appears once, in the response that creates it. States: `OPEN`, then `ACCEPTED`, `REVOKED` or `EXPIRED`. A
  background job (`services/invitation_cleanup_job_impl.py`, hourly) expires overdue invitations; at start-up the
  bootstrap of README 6.9 invites the first OSP Admin from `BOOTSTRAP_ADMIN_FILE`.
- **Accepting with a mandate.** `POST /invitations/accept` takes either the code or a verification attestation of the
  EBW-Connector (C5-M1) with the purpose `representation`: a person showed a mandate of a company in their wallet.
  `services/attestation_check.py` checks the attestation (format, type, issuer, signature, audience, times, claims,
  purpose, client, age); the keys come from `managers/gateways/attestation_keys_impl.py`. The service then compares
  the person with the token, asks C3-M1 for the one `ACTIVE` company with the identifier of the mandate
  (`find_identifier_matches`) and accepts the newest open invitation of that company for this person. The
  invitation and its roles stay required; only the code is replaced. Without `ATTESTATION_ISSUER` no attestation is
  accepted. This way is not in the spec yet (OPEN-QUESTIONS 14).
- **App clients.** `create-client-template` keeps the app roles of an app; `create-instance-client` creates a
  disabled instance client from it, which the enable, disable and update steps change (README 6.1 to 6.4).
- **Concurrency.** `DaoService.lock(...)` takes the locks of README 6.14 in a fixed order (advisory locks in
  PostgreSQL; no-ops in the in-memory backend).

### Folder map

| Folder | Content |
|---|---|
| `controllers/` | HTTP only, one folder per path segment of `/api/app-access`: `companies/` (users, portal roles, app roles, invitations of one company), `invitations/` (`/invitations/accept`), `osp/` (users, companies, staff, staff invitations), `internal/` (queries), `steps/` (Process Orchestration). Mounted and checked against the spec by `portal_common.routing.mount()`. |
| `services/` | business rules: `user_service_impl.py` (bindings, portal and staff roles, app roles), `invitation_service_impl.py` (invitations, bootstrap), `app_client_service_impl.py` (templates, instance clients), `invitation_cleanup_job_impl.py`, `validation.py`, `context.py` (shared context, audit and role logs), `module.py` (wiring), `actors.py` (scope and actor of a call), `ports/` (service interfaces) |
| `managers/` | state and adapters: `config/` (`application.properties`, read through `Config`), `dao/` (DAO interfaces and their implementation on the SQLModel tables in `sql.py`, the only code with database sessions), `database.py` (`portal_common.database` sessions, transactions, advisory locks), `migrations/` (Alembic, PostgreSQL), `iam/` (Keycloak Admin API or the in-memory test IAM), `gateways/` (C3-M1 and C10-M1 through `portal_common.neighbours`), `data/` (stand-in companies and subscriptions), `ports/` (adapter interfaces) |
| `models/` | pydantic models of the responses on `portal_common.models.ApiModel` (camelCase in JSON): people, invitations, app clients, step results; `Page` and `StepResult` from `portal_common.models`; value sets in `constants/`; the SQLModel tables in `tables.py`; the internal records the services work on in `internal/`; exceptions in `exception/` and their Problem Details in `exception_translator.py` |

### In-process interface

`interface.py` holds the steps (`create_client_template`, `create_instance_client`, `enable_instance_client`,
`disable_instance_client`, `update_instance_url`, `add_app_roles`, `update_role_descriptions`,
`assign_company_admin`, `disable_company_users`, `enable_company_users`) and the queries (`list_app_roles`,
`list_app_instance_clients`, `get_app_instance_client`, `list_company_user_refs`) of the call convention. Errors leave
as Problem Details with type `urn:c2-m2:problem:<name>`; steps always carry `retryable`.

### Events

Published with source `urn:c2-m2` (README 10): `UserAssignedToCompany`, `UserRemovedFromCompany`, `UserRolesChanged`,
`OspStaffRolesChanged`, `CompanyUsersDisabled`, `CompanyUsersEnabled`, `AppClientTemplateCreated`,
`AppInstanceClientCreated`, `AppInstanceClientEnabled`, `AppInstanceClientDisabled`, `AppInstanceUrlUpdated`,
`AppRolesAdded`, `AppRoleDescriptionsUpdated`. It consumes no events.

### Configuration and persistence

`managers/config/application.properties` maps the variables of README section 4 (`C2_M2_CONFIG_FILE` names another
file): `APP_ACCESS_DATABASE_URL`, `C2_M2_DATABASE_URL` or `DATABASE_URL`, `IAM_URL`, `IAM_REALM`, `C2_M2_CLIENT_ID`, `C2_M2_CLIENT_SECRET`,
`PORTAL_CORE_CLIENT_ID`, the role names, the invitation limits (`INVITATION_TTL_HOURS`, `INVITATION_MAX_OPEN`, ...),
`BOOTSTRAP_ADMIN_FILE`, the client ID prefixes and scopes, `LANGUAGES` and `QUERY_MAX_APPS`, and for accepting with a
mandate `ATTESTATION_ISSUER`, `ATTESTATION_JWKS_URL`, `ATTESTATION_JWKS_FILE`, `ATTESTATION_AUDIENCE`,
`ATTESTATION_CLIENT_IDS`, `ATTESTATION_CLOCK_SKEW_SECONDS`, `ATTESTATION_JWKS_CACHE_SECONDS` (the names of the
registration, so one value per installation serves both) and `INVITATION_ATTESTATION_MAX_AGE_MINUTES`. The data is in the
SQLModel tables of `models/tables.py` (`portal_common.database`): with a database URL in PostgreSQL (driver `pg8000`,
schema upgraded by Alembic at start, version table `alembic_version_c2_m2`), without one in a private in-memory
SQLite database, which starts empty and is emptied by `reset()`; bootstrap and invitation cleanup only run with a
database URL. Without `IAM_URL` the in-memory test IAM stands in for Keycloak.
Neighbours come from `C3_M1_URL`, `C10_M1_URL` or `MODULE_URLS`; an empty address uses the stand-in data.

### Run and test

```bash
RUNTIME=app_access uv run python -m runtimes          # this feature alone, API under /api/app-access
uv run pytest -q tests/test_c2_m2_*.py
```

## Links

- [Spec README](../../spec/C2-M2-AppAccess/README.md) and [openapi.yaml](../../spec/C2-M2-AppAccess/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

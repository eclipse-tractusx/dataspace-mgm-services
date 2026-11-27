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

# C2-M2 Users and App Access: open questions

Points where the spec (`spec/C2-M2-AppAccess`, version 0.2) is unclear or where this implementation had to choose a reading.

| No. | Question | Spec | Reading implemented | Who decides |
|---|---|---|---|---|
| 1 | Own database `c2_m2` in PostgreSQL (`DATABASE_URL`). | README 4, 5 | The tables of README 5 are SQLModel classes (`models/tables.py`) in the feature's own database of `portal_common.database` (`APP_ACCESS_DATABASE_URL`, `C2_M2_DATABASE_URL`, then `DATABASE_URL`). PostgreSQL through SQLAlchemy with the driver `pg8000`; the schema is versioned with Alembic (`managers/migrations/`, version table `alembic_version_c2_m2`, initial revision generated from the tables) and upgraded to `head` at start. The services reach the database only through `DaoService` (`ctx.dao`): it holds every DAO (`managers/dao/sql.py`), and `ctx.dao.lock(...)` takes the locks of 6.14 in their fixed order through the DAOs (`templates.lock`, `companies.lock`, `invitations.lock_staff`/`lock`, `company_users.lock_account`) as transaction-scoped advisory locks (`pg_advisory_xact_lock`) inside one session transaction. Domain errors commit what was saved before them (for example the failed name check of 7.10); other errors roll back. **Without a database URL**: the same tables in a private in-memory SQLite database, whose transactions run one after the other; `demo.py` and the tests need no PostgreSQL. `reset()` empties the tables. The partial unique indexes of the old hand-written schema (one `SINGLE` client per app, one current binding per account) are not in the tables; the services keep both rules. | Team, spec authors |
| 2 | `SUBSCRIPTION_URL` and `COMPANY_URL` name the neighbour addresses. | README 4, 11.2 | The module does not read them (AGENTS.md rule 6); `portal_common.neighbours` resolves `C10_M1_URL`, `C3_M1_URL` and `MODULE_URLS`. Empty address = built-in stand-in. | Scaffold |
| 3 | Files of the built-in stand-ins have no configuration variable in section 4 (C1-M3 has `STUB_*_FILE`). | README 11.2, 14.2 | Fixed files `stub-subscriptions.json` and `stub-companies.json` in `managers/data/`, with the test values of 14.2. | Spec authors |
| 4 | 7.16 requires a binding to the OSP company before direct staff roles; 6.7 limit 4 also allows accounts without a company. | README 6.7, 7.16 | 7.16 as written: without a staff role yet, only accounts bound to `ospCompanyId`; others are invited (7.17). | Spec authors |
| 5 | Without `IAM_URL` there is no Admin API. | README 11.1, 14.1 | With `IAM_URL` set: calls Keycloak (`KeycloakPortalIam`) at the reachable Admin API. Without `IAM_URL`: delegates to the in-memory `tools.test_iam.iam()` via `TestIamPortalIamAdapter` (`managers/iam/test_iam_portal_iam.py`), enabling stand-in / `--small-iam` execution of `demo.py` without requiring Docker Keycloak. | Team |
| 6 | Errors of a neighbour: README 11.2 says 502 `upstream-error`; the shared rule gives 502 `neighbour-rejected` for a 4xx answer. | README 11.2, 12 | Shared rule of `portal_common.neighbours`; a 404 of C3-M1 counts as "company not active". | Scaffold, spec authors |
| 7 | `assign-company-admin` on a binding `DISABLED`: which event? | README 8.8 step 5 | `UserAssignedToCompany` with `via` `ONBOARDING` and the restored portal roles; on a binding `ACTIVE` only `UserRolesChanged` if `Company Admin` was added. | Spec authors |
| 8 | 9.1 `templateExists` for a template whose creation was interrupted (row without `iam_client_uuid`). | README 9.1 | `false`, as for an app without a template. | Spec authors |
| 9 | 7.12 `portalRoles` and `staffRoles`. | README 7.12 | `portalRoles` = company portal roles only, `staffRoles` = staff roles; `Applicant` in neither. | Spec authors |
| 10 | 7.5: which instance clients count as target clients of a single-instance app. | README 6.10 | The one `SINGLE` client with status `ACTIVE`, if the company has any active subscription to the app. | Spec authors |
| 11 | Events of C2-M2 run as a runtime of its own (`main.py`, `RUNTIME=app_access`, FRAMEWORK 4.7). FRAMEWORK 6 says a split-out module delivers its CloudEvents to `POST /api/v1/events/inbox` of the installation with the token of `svc-c2-m2`, but section 4 of the README names no variable for the address of that inbox, and `portal_common.events` has no forwarding. | FRAMEWORK 4.7, 6; README 4, 10 | The own runtime publishes into its own in-process relay only; nothing leaves the process. Inside the installation (scaffold) events flow as before. A configuration variable and forwarding belong in `portal_common` and the spec, not in this module. | Spec authors, scaffold |
| 12 | FRAMEWORK 4.1, base path `/api/c2-m2` "until the common path convention is settled". | FRAMEWORK 4.1 | Served under the readable feature name `/api/app-access` (ADR-0003, decision 2); `/api/c2-m2` answers 404. Problem types, event sources, permissions and the service account `svc-c2-m2` keep the spec id. | Spec authors |
| 13 | The hackathon module split the spec into a public (`openapi.yaml`) and a private (`openapi-private.yaml`, `/internal`, `/steps`) contract with its own router per half. | FRAMEWORK 4.7 | Dropped with the migration: nothing mounted the halves separately. `mount()` checks every operation against the spec's `openapi.yaml`; the private paths are the ones under `/internal/` and `/steps/`, which an ingress can block by prefix. | Team |
| 14 | Accepting an invitation with a mandate: `POST /invitations/accept` with `attestation` in place of `code`. The spec (version 0.2) knows only the code; its `openapi.yaml` requires `code` in the body. | README 6.8, 7.10; C5-M1 6.5, 9.1 | Implemented as described in the feature README and in the draft of version 0.3 (6.8a): the operation and its permission stay, the body carries exactly one of `code` and `attestation`, new errors `attestation-invalid` (400, with `reason`) and `representation-not-confirmed` (403, with `reasons`). The `jti` of the attestation is not stored; the attestation is accepted for `INVITATION_ATTESTATION_MAX_AGE_MINUTES` only. A mandate revoked later does not end the binding. | Spec authors |

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

# Company Profile (C3-M1)

Migrated from `modules/c3_m1/` (spec `spec/C3-M1-CompanyProfile`).

## What it does

The company profile keeps the record of every company of an onboarding service provider's installation, from the
application to the deactivation: name, address, identifiers, the source of the core data, the BPN assigned by the
core service provider, the status and the company roles with the consents they need. It is the only place that
stores and changes this data; other modules keep only the `companyId` and read the rest here.

Callers:

- **Process Orchestration** (C12-M1) runs the steps of README 8: create, take over the BPN, activate, reject,
  deactivate and reactivate a company.
- **People of a company** (UI) read their own company and its roles; a Company Admin changes the short name,
  updates core data with a verification attestation of the EBW-Connector, submits change requests with documents
  and adds or removes company roles with their consents.
- **OSP staff** (UI) search and read all companies, correct and deactivate them (`OSP Admin`) and review change
  requests (`OSP Reviewer`, `OSP Admin`).
- **Other modules** (C1-M2, C1-M3, C2-M3, C4-M1, C4-M2, C6-M1, C8-M1, C10-M1) read one or many companies, search for duplicate identifiers and
  read the role catalogue (README 9).

## How it works

### Flows and states

- Company status (README 6.1): `REQUESTED` (step `create-company` from a submitted application of C1-M2) ->
  `ACTIVE` (`activate-company`, after `assign-identifier` took over the BPN) -> `INACTIVE` (`deactivate-company`
  with reason `MANUAL` or `TRANSFERRED`, or staff deactivation 7.13) -> `ACTIVE` again (`reactivate-company` from a
  `REACTIVATION` or `TRANSFER` application). `REQUESTED` -> `REJECTED` (`reject-company`) is final and frees the BPN.
- Steps are idempotent (FRAMEWORK 4.4): a repetition returns the stored result and publishes nothing.
- Core data changes: with an attestation immediately (7.3, source `EBW`); otherwise through a change request
  `OPEN` -> `APPROVED` / `DECLINED` (OSP staff, four eyes) or `WITHDRAWN` (the company); at most one `OPEN` request
  per company. A correction by OSP staff (7.12) switches the source to `MANUAL`.
- Company roles (7.7 to 7.9): a role assignable by the company needs the consents to the active terms of C1-M2 in
  their current version; removing a role keeps the row as `INACTIVE` and ends consents no other role needs.
- Every changing operation, every step and every document read writes the audit log (FRAMEWORK 4.3); a changing
  call holds the lock of README 6.9 on the company.

### Folder map

| Folder | Content |
|---|---|
| `controllers/companies/` | `/companies/{companyId}` (7.1 to 7.3), `.../change-requests` (7.4 to 7.6), `.../company-roles` (7.7 to 7.9), scope `company` |
| `controllers/osp/` | `/osp/companies` (7.10 to 7.13), `/osp/change-requests` with `documents/` (7.14 to 7.18) |
| `controllers/internal/` | `/internal/companies` (9.1 to 9.3), `/internal/company-roles` (9.4) |
| `controllers/steps/` | `/steps/*` (README 8) |
| `services/` | `company_lifecycle_service` (steps, staff deactivation, seed data), `company_service` (7.2, 7.3, 7.10, 7.12), `change_request_service`, `company_role_service`, `company_query_service` (9.1 to 9.4), `company_views` (response models of a company), `company_validation` and `company_changes` (field and identifier rules of 5, 6.3, 6.4), `attestation_verifier` (6.7) |
| `managers/` | `company_repository` (the only code that opens the database), `config` (environment and installation settings), `data/stub-applications.json` (stand-in of C1-M2) |
| `models/` | `value_sets` (enums of the spec), `company`, `change_request`, `company_role`, `steps` (pydantic response and step result models on `portal_common.models`), `tables` (SQLModel tables) |

Request bodies stay `dict` at the controller: the spec's answers to a bad body (`409 field-locked`, `400` with
`errors[].reason`, `400 consent-missing`) come from `services/company_validation.py` and would change if pydantic
refused the body first. Responses are the models of `models/`, declared as the return type of each operation.

### Interface

`interface.py` (call convention): the steps `create_company`, `assign_identifier`, `activate_company`,
`reject_company`, `deactivate_company`, `reactivate_company` and the queries `query_company`, `query_companies`,
`find_identifier_matches`, `query_company_role_catalog`. An in-process call answers the same JSON the HTTP API sends
(`models.wire`).

### Events

Published: `CompanyCreated`, `CompanyIdentifierAssigned`, `CompanyActivated`, `CompanyRejected`,
`CompanyDeactivated`, `CompanyReactivated`, `CompanyRolesChanged`, `CompanyDataChanged`,
`CompanyChangeRequestSubmitted`, `CompanyChangeRequestClosed`. Consumed: none. Neighbour calls: C1-M2
(`get_application_internal`, `list_agreements_internal`), with the built-in stand-in when C1-M2 has no address.

### Configuration

Read at call time in `managers/config.py` (README 4): `LANGUAGES`, `QUERY_MAX_COMPANIES`, `REGISTRATION_URL`,
`COMPANY_ROLES_FILE`, `CHANGE_REQUESTS_ENABLED`, `CHANGE_REQUEST_MAX_DOCUMENTS`, `CHANGE_REQUEST_MAX_DOCUMENT_BYTES`,
`ATTESTATION_ISSUER`, `ATTESTATION_AUDIENCE`, `ATTESTATION_CLIENT_IDS`, `ATTESTATION_JWKS_URL`,
`ATTESTATION_JWKS_FILE`, `ATTESTATION_MAX_AGE_HOURS`, `ATTESTATION_CLOCK_SKEW_SECONDS`,
`ATTESTATION_JWKS_CACHE_SECONDS`, `STUB_APPLICATIONS_FILE`; from the installation settings `ospCompanyId`,
`ospCompanyFile` (seed data) and `dataspace.name`.

### Persistence

The tables of README 5 (`company`, `company_identifier`, `company_role_assignment`, `consent`, `change_request`,
`change_request_document`, `used_attestation`, `audit_log`) are SQLModel classes in `models/tables.py` on the
feature's own base (F17). The database is chosen at call time by `portal_common.database`:
`COMPANY_PROFILE_DATABASE_URL`, then `C3_M1_DATABASE_URL`, then `DATABASE_URL`; without one a private in-memory
SQLite database. `on_startup()` creates missing tables and writes the seed of the OSP company if it is missing;
`reset()` empties the tables and writes the seed again. The invariants of README 5 are checked in the repository
and backed by indexes (one BPN among companies that are not `REJECTED`, one `OPEN` change request per company).
On PostgreSQL the lock of 6.9 is also a session advisory lock, so replicas exclude each other. There are no
migrations yet: the tables are created from the models.

### Run and test it alone

```bash
RUNTIME=company_profile uv run python -m runtimes
uv run pytest -q tests/test_c3_m1_*.py
TEST_DATABASE_URL=postgresql://postgres:pg@localhost:55432/company_profile uv run pytest -q tests/test_c3_m1_store_backend.py
```

## Links

- [Spec README](../../spec/C3-M1-CompanyProfile/README.md) and [openapi.yaml](../../spec/C3-M1-CompanyProfile/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

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

# Registration (C1-M2)

Migrated from `modules/c1_m2/` (spec `spec/C1-M2-Registration`).

## What it does

A company applies to join the dataspace at its onboarding service provider (OSP). The applicant signs in with
their own token, fills in the application and proves the company either with a verification attestation of the
Business Wallet (verification path `EBW`) or with uploaded supporting documents (`DOCUMENTS`). The feature checks
the attestation, compares the declared company data with it, records the requested company roles and the
consents to the required terms, and publishes the events of the application. It also keeps the versions of the
terms and serves the reference data of the registration form.

Callers:

| Who | What for |
|---|---|
| applicant (`Applicant`) | reference data and terms; create, change, read, submit and withdraw the own application; replace the attestation; upload supporting documents |
| OSP staff (`OSP Reviewer`, `OSP Admin`) | read every application and its documents; `OSP Admin` creates versions of the terms |
| Process Orchestration (C12-M1) | steps `complete-application` and `close-application` |
| C1-M3 Application Review | queries `get_application_internal`, `list_applications_internal` |
| C3-M1 Company Profile | queries `get_application_internal`, `list_agreements_internal` |

## How it works

### Flow and states

```
CREATED --submit--> SUBMITTED --complete-application--> COMPLETED
   |                    |------close-application-----> DECLINED
   +------withdraw------+---------------------------> WITHDRAWN
```

`POST /applications` runs the checks of README 7.2 in their order: 403 for an account already bound to a
company, the body (6.2), `documents-disabled`, the attestation (6.4, ten checks, the first failure gives the
`reason`), one open application per person and one application per attestation (6.11), the existing company
for `REACTIVATION` and `TRANSFER` (C3-M1), the company data and its comparison with the attestation (6.5), the
reference data (6.6, 6.7). A repetition with the same attestation answers 200 with the open application.
Changes (`PATCH`, `PUT .../attestation`, documents) are only allowed in `CREATED`. `submit` checks that the
attestation is still usable (`ATTESTATION_MAX_AGE`) or, for `DOCUMENTS`, that a commercial register extract and
the declaration of representation are there, and that the consents name exactly the active versions of the
required terms (6.8). `withdraw` of a submitted application asks C1-M3 whether the review has already decided.

### Folder map

| Folder | Content |
|---|---|
| `controllers/` | HTTP under `/api/registration`, each operation calls one function of `interface.py`: `countries/`, `company_roles/`, `agreements/` (form data, 7.1); `applications/` with `documents/` (own applications, 7.2 to 7.11); `osp/applications/` with `documents/` and `osp/agreements/` (OSP staff, 7.12 to 7.16); `steps/` (README 8); `internal/applications/`, `internal/agreements/` (queries, README 9) |
| `services/` | `application_service` (create, change, withdraw, scope `own`), `submission_service` (7.10), `application_validation` (input checks of 6.2, 6.6, 6.7), `company_data` (company data and comparison, 6.5, 6.9), `attestation_verifier` (the checks of 6.4, JWKS cache, repeated signature check), `document_service` (7.7 to 7.9, 7.14), `agreement_service` (7.15, 7.16), `reference_data_service` (7.1), `application_process_service` (steps and queries), `application_views` (rows to views), `shared` (clock, audit entry, paging, JSON form) |
| `managers/` | `application_repository` (applications, document bytes, used attestations, audit log; the only code that opens a session), `agreement_repository` (versions of the terms), `reference_catalog` (countries, identifier types, company roles, initial terms, read-only), `neighbour_client` (C3-M1 and C1-M3 with their built-in stand-ins), `config` (every environment variable) |
| `models/` | `applications` (request bodies and the views `Application`, `ApplicationWithReview`, `ApplicationInternal`, `ApplicationSummary`), `reference_data` (countries, roles, `Agreement`, `AgreementVersion`, `AgreementVersionCreate`), `steps` (step input and result), `value_sets` (`str` enums), `errors` (the Problem factories of README 12, reading a checked body into its model), `tables` (SQLModel tables) |

The request bodies are taken as JSON and checked by the services first, so that 403, 404 and 409 come before
field errors and the field errors carry the messages of README 6; the checked body is then read into its model
(`ApplicationCreate`, `ApplicationUpdate`, `SubmitRequest`, `AgreementVersionCreate`, `ApplicationStep`). The
responses are declared as `response_model` with `response_model_exclude_unset`, so a field the stored object
never had stays out of the JSON, as before. Lists are `Page[...]` of `portal_common.models`, the step results
`StepResult[ApplicationStepResult]`.

### Interface

`interface.py` (call convention): the steps `complete_application(input)` and `close_application(input)`, and
the queries `get_application_internal(applicationId=...)`, `list_applications_internal(applicationId=[...])`
and `list_agreements_internal(status=...)`; they return the same JSON as the HTTP API. It also re-exports the
operations of people (`create_application`, `submit_application`, `upload_document`, ...), which only the
controllers call and which return the response models.

### Events

Published (CloudEvents with source `urn:c1-m2`, README 10): `ApplicationCreated`, `ApplicationSubmitted`,
`ApplicationWithdrawn` (only after submission), `ApplicationCompleted`, `AgreementVersionActivated`. None are
consumed.

### Configuration

Read in `managers/config.py` at call time: `ATTESTATION_ISSUER`, `ATTESTATION_AUDIENCE`,
`ATTESTATION_ALGORITHMS`, `ATTESTATION_CLIENT_IDS`, `ATTESTATION_MAX_AGE` (an invalid value stops the start),
`ATTESTATION_CLOCK_SKEW_SECONDS`, `ATTESTATION_JWKS_CACHE_SECONDS`, `ATTESTATION_JWKS_URL`,
`ATTESTATION_JWKS_FILE`, `DOCUMENTS_ENABLED`, `DOCUMENT_MAX_BYTES`, `DOCUMENT_MAX_COUNT`, `CATALOG_FILE`,
`STUB_COMPANIES_FILE`, `STUB_REVIEWS_FILE`. Neighbour addresses (`C3_M1_URL`, `C1_M3_URL`, `MODULE_URLS`) are
resolved by `portal_common.neighbours`; the countries and identifier types come from `masterDataFile` of the
installation settings.

### Persistence

The feature has its own database through `portal_common.database`: `REGISTRATION_DATABASE_URL`, then
`C1_M2_DATABASE_URL`, then `DATABASE_URL` (PostgreSQL), otherwise a private in-memory SQLite database. Tables
(`models/tables.py`): `application` (one row per application; company data, comparison, document metadata,
consents and the attestation extract as JSON columns), `application_document` (the bytes),
`used_attestation`, `audit_log`, `agreement_version` (seeded with the initial terms when empty). `on_startup()`
creates the tables, `reset()` empties them and seeds the terms again. A module-wide lock serialises the changes
(6.11); on the in-memory database the units of work also take turns, since it has one connection for all
threads.

### Run and test it alone

```bash
RUNTIME=registration uv run python -m runtimes
uv run pytest -q tests/test_c1_m2_*.py
```

## Links

- Spec: [README](../../spec/C1-M2-Registration/README.md), [openapi.yaml](../../spec/C1-M2-Registration/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003 feature-first layout and runtimes](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

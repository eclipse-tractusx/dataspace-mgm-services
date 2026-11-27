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

# Application Review (C1-M3)

Migrated from `modules/c1_m3/` (spec `spec/C1-M3-ApplicationReview`).

## What it does

The application review decides whether a company that applied at the onboarding service provider (OSP) may join.
For every submitted application of the registration (C1-M2) it opens one review case, runs an automatic pre-check
(attestation, representation, company data, duplicates in the installation and at the CSP, consents) and records
the result per check. OSP staff then approve the application or decline it with a reason; in configured cases two
different people must approve (four-eyes principle), and nobody decides on their own application. The decision is
published as an event, and Process Orchestration continues the onboarding from there.

Callers:

| Who | What for |
|---|---|
| Process Orchestration (C12-M1) | step `open-review` after `ApplicationSubmitted`, step `close-review` after `ApplicationWithdrawn` |
| OSP staff, role `OSP Reviewer` (`view_reviews`, `review_application`) | list and read review cases, approve, decline |
| OSP staff, role `OSP Admin` (`view_reviews`) | list and read review cases |
| Registration (C1-M2) | query `get_review_status_by_application` |

## How it works

### Flow and status

```
open-review ──> OPEN ──approve (no four-eyes case)──────────────> APPROVED     event ApplicationApproved
   │             │  └─approve (four-eyes case)──> AWAITING_SECOND_APPROVAL ──approve by another person──> APPROVED
   │             ├─automatic approval (AUTO_APPROVE_KINDS, EBW, all PASSED, no four-eyes case) ──> APPROVED
   │             └─decline (also from AWAITING_SECOND_APPROVAL) ──> DECLINED   event ApplicationDeclined
   └─ withdrawn application, or close-review ──> CLOSED
```

`APPROVED`, `DECLINED` and `CLOSED` are final. A first approval in a four-eyes case publishes
`ApplicationAwaitingSecondApproval` (OP-49). `open-review` is idempotent: it runs only the checks that have no result
yet or ended with `ERROR`, and answers 502 while a check is `ERROR` (`neighbour-rejected`, not retryable, when every
such neighbour rejected the request; `upstream-error`, retryable, otherwise).

### Folder map

| Folder | Content |
|---|---|
| `controllers/review_cases/` | `GET /review-cases`, `GET /review-cases/{reviewCaseId}`, `POST /review-cases/{reviewCaseId}/approve`, `POST /review-cases/{reviewCaseId}/decline` |
| `controllers/steps/` | `POST /steps/open-review`, `POST /steps/close-review` |
| `controllers/internal/review_cases/` | `GET /internal/review-cases?applicationId=...` |
| `services/review_cases.py` | status rules, four-eyes principle, own application, automatic approval, decisions, steps, query, audit log entries, events; returns the API models |
| `services/checks.py` | the six checks of the pre-check (README 6.2) and the evaluation of the CSP matches (README 6.3) |
| `managers/review_case_repository.py` | the only code that opens a database session: review cases (looked up by id or application), paged lists, audit log; its lock stands for the row lock of README 6.8 |
| `managers/neighbour_client.py` | calls to C1-M2, C3-M1 and C3-M2 through `portal_common.neighbours`, with the built-in stand-in files |
| `managers/config.py` | the configuration of README 4 |
| `models/` | `value_sets.py` (status, kind, check keys and results as `StrEnum`), `errors.py` (the Problem factory), `validation.py` (in-process step input into the step models, 400 `validation`), `requests.py` (`ApproveRequest`, `DeclineRequest`, the step inputs `OpenReviewStep`, `CloseReviewStep` on `StepRequest`), `review_case.py` (`ReviewCase`, `ReviewCaseSummary`, `ReviewCasePage` = `Page[ReviewCaseSummary]`, `ReviewStatusInfo`, the step results in `StepResult[...]`), `tables.py` (SQLModel tables `review_case` and `audit_log`) |

All paths are relative to the base path `/api/application-review`.

### In-process interface

`interface.py` is the contract that other modules and Process Orchestration call: the steps `open_review(input)` and
`close_review(input)`, the query `get_review_status_by_application(applicationId=...)`, and the operations of staff
`list_cases`, `get_case`, `approve`, `decline`, plus `reset()` and `config()`. They take the JSON input of the spec
and return the JSON form of the answer (camelCase), the same as over HTTP. The controllers call this interface too
and declare the models as body and `response_model`.

### Events

Published with `source` `urn:c1-m3`: `ApplicationApproved` (with `bpn` of the expected CSP match for `TRANSFER` and
`REACTIVATION`), `ApplicationDeclined` (with `reason`) and `ApplicationAwaitingSecondApproval`. The feature consumes
no events.

### Configuration

Read in `managers/config.py` at call time; an invalid value stops the start (`on_startup()`).

| Variable | Default | Meaning |
|---|---|---|
| `ENABLED_CHECKS` | all six checks | checks of the pre-check; `CSP_MATCH_EXPECTED` always runs for `TRANSFER` and `REACTIVATION` |
| `FOUR_EYES_CASES` | `CHECK_FAILED,DOCUMENTS` | when a second approval is needed (`CHECK_FAILED`, `DOCUMENTS`, `ALWAYS`) |
| `AUTO_APPROVE_KINDS` | empty | kinds approved without staff (`ONBOARDING`, `TRANSFER`; never `REACTIVATION`) |
| `DUPLICATE_CHECK_IDENTIFIER_TYPES` | `EUID,EBWOID,VAT_ID,LEI_CODE` | identifier types of `NO_DUPLICATE` |
| `STUB_APPLICATIONS_FILE`, `STUB_COMPANIES_FILE`, `STUB_CSP_FILE` | unset | stand-in files of C1-M2, C3-M1, C3-M2 when their address is empty |

The neighbour addresses `C1_M2_URL`, `C3_M1_URL`, `C3_M2_URL` (or `MODULE_URLS`) are read by
`portal_common.neighbours`: empty means the stand-in file, `in-process` or a URL calls the neighbour.

### Persistence

The feature's own database through SQLModel (`portal_common.database`): the tables `review_case` (checks, first
approval, decision and closure as JSON columns; indexes on `application_id`, `status` and the opening order `seq`) and
`audit_log` in `models/tables.py`. The URL is read from `APPLICATION_REVIEW_DATABASE_URL`, then `C1_M3_DATABASE_URL`,
then `DATABASE_URL`; without one the feature runs on a private in-memory SQLite database, so tests and `demo.py` need no
server. `on_startup()` creates the tables, `reset()` empties them.

### Run and test

```bash
RUNTIME=application_review uv run python -m runtimes   # serves /api/application-review on PORT (default 8000)
uv run pytest -q tests/test_c1_m3_*.py
```

## Links

- Spec: [README](../../spec/C1-M3-ApplicationReview/README.md), [openapi.yaml](../../spec/C1-M3-ApplicationReview/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

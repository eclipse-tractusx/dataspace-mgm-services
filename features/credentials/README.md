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

# Credentials (C4-M1)

Migrated from `modules/c4_m1/` (spec `spec/C4-M1-Credentials`).

## What it does

The feature triggers the two basic credentials of a company at an issuer, the BPN credential and the membership
credential, tracks their status and revokes the membership credential when the company is deactivated. The
credentials themselves live in the company's dataspace wallet (C4-M2); this feature only stores which credential
was ordered, issued, failed or revoked, and when. Which issuer signs depends on the installation (`ISSUER_MODE`): an
own issuer of the OSP (Credential Issuer or IssuerService), the issuer of the CSP, or the built-in stand-in `STUB`.

Callers:

- **Process Orchestration** (C12-M1): the steps `issue-credentials` (onboarding, reactivation; long-running) and
  `revoke-credentials` (deactivation).
- **People of a company** (UI, scope `company`, `view_credentials`): the status of the own company's credentials.
- **OSP staff** (UI, `manage_credentials`): every credential, filters for failed and open ones, and the
  confirmation of a revocation done by hand.
- **Issuers and callback adapters** (one service account each, `report_credential_status`): the status report
  `POST /issuer-callbacks/{credentialKind}`.
- **Other modules**: the query `query_company_credentials`.

## How it works

### Flows

- **Issue** (README 8.1): the company must be `REQUESTED`/`ACTIVE` with a BPN (C3-M1) and the wallet `ACTIVE` with a
  DID (C4-M2). The route is chosen by the rules of README 6.3. Every type that is not yet `ISSUED` (and not a recent
  `REQUESTED`, see `RESEND_AFTER_HOURS`) is ordered through the route; only after the route accepted the order the
  row becomes `REQUESTED`. The step answers `RUNNING` until every type of the round is `ISSUED`, then `DONE`.
- **Status report** (README 7.4): the issuer reports `SUCCESSFUL` or `UNSUCCESSFUL` for a BPN and kind. `REQUESTED`
  becomes `ISSUED` or `FAILED`; a late success for a `CANCELLED` row is revoked at once. When every type of the round
  is `ISSUED`, the round is `DONE` and `CredentialsIssued` is published once.
- **Revoke** (README 8.2): `ISSUED` is revoked through the route of the order, or becomes `REVOCATION_PENDING` when
  the route cannot revoke (Credential Issuer); open orders become `CANCELLED`. OSP staff confirm a pending
  revocation with `confirm-revocation`, which sets `REVOKED`.

Status per credential (README 6.1): `-`, `FAILED`, `CANCELLED` or `REVOKED -> REQUESTED` (new order, `attempt` + 1);
`REQUESTED -> ISSUED | FAILED`; `FAILED -> ISSUED` (late report); `ISSUED -> REVOKED | REVOCATION_PENDING`;
`REQUESTED | FAILED -> CANCELLED`; `REVOCATION_PENDING -> REVOKED`; a late success for `CANCELLED` is revoked at
once. Every change writes a history row. All operations for one company run under one per-company lock (README 6.6).

### Folder map

| Folder | Contents |
|---|---|
| `controllers/companies/credentials/` | `GET /companies/{companyId}/credentials` (scope `company`) |
| `controllers/credentials/` | `GET /credentials`, `POST /credentials/{credentialId}/confirm-revocation` (OSP staff) |
| `controllers/issuer_callbacks/` | `POST /issuer-callbacks/{credentialKind}` (status reports of the issuers) |
| `controllers/internal/companies/credentials/` | `GET /internal/companies/{companyId}/credentials` (query) |
| `controllers/steps/` | `POST /steps/issue-credentials`, `POST /steps/revoke-credentials` |
| `services/credential_service.py` | the rules of issuing, status reports, revoking and confirming (README 6, 7.3, 7.4, 8) |
| `services/credential_views.py` | the read views of README 7.1, 7.2 and 9.1 |
| `services/issuer_routes.py` | the choice of the route (README 6.3) and the route objects |
| `services/stub_issuer.py` | the built-in stand-in issuer `STUB` (README 11.6): reports in process after a delay |
| `managers/credential_store.py` | `CredentialStore` and its repository `SqlCredentialStore` on the tables, and `store()` |
| `managers/issuer_clients.py` | clients of the Credential Issuer, the IssuerService and the CSP issuer (README 11.3 to 11.5) |
| `managers/neighbour_client.py` | C3-M1 `query_company`, C4-M2 `get_wallet_info` and `get_holder_access` |
| `managers/config.py` | every variable of README 4, read at call time |
| `models/` | pydantic API models of `openapi.yaml` (`credentials.py`: step inputs and results, `IssuerResponse`, the views, `CredentialPage`), SQLModel tables of README 5 (`tables.py`), value sets (`values.py`), spec id, every Problem factory and `parse()` (`errors.py`) |

### In-process interface

`interface.py` holds the call convention: the steps `issue_credentials(input)` and `revoke_credentials(input)` and
the query `query_company_credentials(companyId=...)`, with the JSON of `openapi.yaml` as input and answer (validated
with the models, an invalid input is 400 `validation`), `report_status()` for an issuer in the same process, and
`store()` and `reset()` for tests. The controllers call the model-level functions of the interface (`issue`,
`revoke`, `own_credentials`, `list_credentials`, `confirm_revocation`, `receive_report`, `company_credentials`),
which hand the parsed models to the services and return the API models (`StepResult[IssueResult]`,
`CredentialPage`, ...).

### Events

Published as CloudEvents with `source` `urn:c4-m1` (README 10): `CredentialsIssued` (round `DONE`),
`CredentialIssuanceFailed` (report `UNSUCCESSFUL` for an open order), `CredentialRevoked`. The feature consumes no
events.

### Configuration

Read in `managers/config.py` at call time; the defaults are in `OPEN-QUESTIONS.md` (decision 3):
`ONBOARDING_CREDENTIAL_TYPES`, `RESEND_AFTER_HOURS`, `ISSUER_MODE`, `ISSUER_ROUTES`, `STUB_ISSUER_DELAY_SECONDS`,
`STUB_ISSUER_FAIL_TYPES`, `CALLBACK_BASE_URL`, `CREDENTIAL_FORMAT`, `CSP_ISSUER_URL`, `CSP_ISSUER_DID`,
`CSP_ISSUER_CREDENTIAL_DEFINITIONS`, `CREDENTIAL_ISSUER_URL`, `CREDENTIAL_ISSUER_TOKEN_URL`,
`CREDENTIAL_ISSUER_CLIENT_ID`, `CREDENTIAL_ISSUER_CLIENT_SECRET`, `ISSUER_SERVICE_ADMIN_URL`,
`ISSUER_SERVICE_API_KEY`, `ISSUER_SERVICE_PARTICIPANT_ID`, `ISSUER_SERVICE_CREDENTIAL_DEFINITIONS`, `ISSUER_DID`.
The neighbours are reached through `portal_common.neighbours` (`COMPANY_URL`, `WALLET_URL` or `MODULE_URLS`).

The callback address handed to the issuers is `{CALLBACK_BASE_URL}/api/credentials/issuer-callbacks/{credentialKind}`.

### Persistence

The feature's own database through SQLModel (`portal_common.database`): the tables `credential`,
`credential_history`, `issuance_run` and `audit_entry` of README 5 in `models/tables.py`, with one `MetaData` for
the feature. `on_startup()` creates them, `reset()` empties them. The URL is `CREDENTIALS_DATABASE_URL`, then
`C4_M1_DATABASE_URL`, then `DATABASE_URL`; without one the feature runs on a private in-memory SQLite database, so
the tests and `demo.py` need no server. `SqlCredentialStore` is the only code that opens a session.

### Run and test

```bash
RUNTIME=credentials uv run python -m runtimes      # the API under /api/credentials, port 8000 (PORT)
uv run pytest -q tests/test_c4_m1_*.py
```

## Links

- Spec: [README](../../spec/C4-M1-Credentials/README.md), [openapi.yaml](../../spec/C4-M1-Credentials/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

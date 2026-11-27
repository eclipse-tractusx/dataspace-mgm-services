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

# Dataspace Wallet Interface (C4-M2)

Migrated from `modules/c4_m2/` (spec `spec/C4-M2-DataspaceWalletInterface`).

## What it does

The feature connects the installation of the onboarding service provider (OSP) with the dataspace wallets of the
companies. It creates one dataspace wallet per company at a provider (SAP DIV, a Tractus-X IdentityHub of the OSP or
the dataspace wallet of the CSP), checks its `did:web` DID and DID document, and creates and deletes wallet accounts
for technical users. The credentials of a wallet account are stored encrypted until a person of the company
retrieves them exactly once.

Who calls it:

- **Process Orchestration** (C12-M1) runs the steps `create-wallet`, `create-wallet-account` and
  `delete-wallet-account` (onboarding and wallet access flows).
- **People of a company** (UI, scope `company`) read the wallet of their company and the wallet account of a
  technical user, and retrieve the account credentials once.
- **C4-M1 Credentials** asks for the wallet and the holder access it needs to issue credentials; **C2-M3 Technical
  User** and others ask for the wallet and the wallet account.
- **SAP DIV** (middleware, client `SAP_DIV_CALLBACK_CLIENT_ID`) reports created wallets and created or deleted wallet
  accounts by callback.

## How it works

**Wallet** (README 6.2, 6.4): `create-wallet` reads the company (BPN, name) from C3-M1, chooses the provider
(`provider` of the input, else `DEFAULT_PROVIDER`, it must be in `ENABLED_PROVIDERS`) and orders the wallet.
`REQUESTED` waits for the provider (SAP DIV answers by callback, IdentityHub and CSP at once), `VALIDATING` checks the
DID form and resolves the DID document, `ACTIVE` publishes `DataspaceWalletCreated`. Wrong DID, invalid document,
unresolvable DID or a missing callback end in `FAILED` with `DataspaceWalletFailed`; the step can start a new attempt.
The step answers `RUNNING` until the wallet is `ACTIVE` (then `DONE`).

**Wallet account** (README 6.3): `REQUESTED`, `ACTIVE` (credentials `AVAILABLE`), `FAILED`, `DELETING`, `DELETED`,
with the events `WalletAccountCreated`, `WalletAccountFailed`, `WalletAccountDeleted` and
`WalletAccountDeletionFailed`. Steps and callbacks of one technical user never run at the same time.

**Scheduled tasks** (README 6.10): a background timer, started by `on_startup()`, fails orders past the callback
deadline, repeats due DID checks and deletes credentials nobody retrieved.

Folder map:

| Folder | Content |
|---|---|
| `controllers/companies/wallet/` | `GET /companies/{companyId}/wallet` |
| `controllers/technical_users/wallet_account/` | `GET /technical-users/{technicalUserId}/wallet-account`, `POST .../credentials` |
| `controllers/callbacks/sap_div/` | `POST /callbacks/sap-div/wallets/{bpn}`, `POST /callbacks/sap-div/technical-users/{externalId}[/delete]` |
| `controllers/steps/` | `POST /steps/create-wallet`, `/steps/create-wallet-account`, `/steps/delete-wallet-account` |
| `controllers/internal/` | `GET /internal/wallets/{companyId}[/holder-access]`, `GET /internal/technical-users/{technicalUserId}/wallet-account` |
| `services/wallet_service.py` | the clock `now()`, provider choice, create-wallet, DID check, wallet callback, timer, wallet queries |
| `services/account_service.py` | wallet accounts: steps, account callbacks, views, one-time credentials, account timer tasks |
| `services/callback_service.py` | checks that a callback comes from the SAP DIV client, then hands it to the services |
| `managers/wallet_store.py` | `WalletStore` contract and `DatabaseStore`, the repository of the tables (the only code with a database session) |
| `managers/crypto.py` | AES-256-GCM encryption of the secrets (`SECRETS_KEY`, `SECRETS_KEY_VERSION`) |
| `managers/did_resolver.py` | DID form and document checks, resolution (`TEST_DID_DOCUMENTS_DIR`, `DID_RESOLVER_URL`, did:web) |
| `managers/providers/` | one adapter per provider (`sap_div`, `identity_hub`, `csp`) with built-in stand-ins, `STUB_FAILURES` |
| `managers/config.py` | the variables the services read |
| `models/` | `MODULE`; `value_sets.py` (the enums of openapi.yaml as `Literal`); `api.py` (pydantic models on `portal_common.models`: step inputs `CreateWalletInput`, `WalletAccountInput`, step results, `Wallet`, `WalletInfo`, `WalletAccount`, `WalletAccountCredentials`, `HolderAccess`); `tables.py` (SQLModel tables) |

`/wallet-control-challenges` (own wallet, later in the spec) is not implemented and answered by the stand-in of the
spec with 501.

In-process interface (`interface.py`, call convention of the root `AGENTS.md`): the steps `create_wallet`,
`create_wallet_account`, `delete_wallet_account` and the queries `get_wallet_info`, `get_holder_access`,
`get_wallet_account_internal`, plus `wallet_view`, `store()` and `reset()`.

Events: publishes the six events above with source `urn:c4-m2`; consumes none.

Configuration (read at call time): `DID_VALIDATION_INTERVAL_MINUTES`,
`DID_VALIDATION_MAX_HOURS`, `PROVIDER_CALLBACK_TIMEOUT_MINUTES`, `TIMER_INTERVAL_SECONDS`,
`ACCOUNT_CREDENTIALS_RETENTION_DAYS`, `BDRS_PUBLIC_URL`, `SAP_DIV_CALLBACK_CLIENT_ID` (`managers/config.py`); the
provider choice `ENABLED_PROVIDERS`, `DEFAULT_PROVIDER` and the provider variables `SAP_DIV_*`, `IDENTITYHUB_*`, `CSP_WALLET_URL` and `STUB_CALLBACK_DELAY_SECONDS` in
`managers/providers/`; `SECRETS_KEY*` in `managers/crypto.py`; `DID_RESOLVER_URL`, `TEST_DID_DOCUMENTS_DIR` in
`managers/did_resolver.py`. Unset values and their defaults are listed in `OPEN-QUESTIONS.md`.

Persistence: the feature's own database through SQLModel (`portal_common.database`): the tables
`dataspace_wallet`, `wallet_secret`, `wallet_account`, `wallet_account_credentials`, `audit_log` and `step_log` of
README 5 in `models/tables.py`, with indexes on the columns looked up by (BPN, DID, status, technical user, wallet).
The URL is `DATASPACE_WALLET_INTERFACE_DATABASE_URL`, then `C4_M2_DATABASE_URL`, then `DATABASE_URL`; without one the
feature runs on a private in-memory SQLite database. `on_startup()` creates the tables, `reset()` empties them. Rows
reach the services as dicts with the column names of the spec; secrets are only stored as ciphertext.

Models: the controllers declare the step inputs as request bodies and the responses as `response_model`; the
services return the models and `interface.py` answers their JSON form. The SAP DIV callback bodies stay plain JSON
objects checked by the services, because README 7.6 wants 403 for a foreign client before any body check and 204
with `FAILED` for an invalid DID document.

Run it alone and test it:

```bash
RUNTIME=dataspace_wallet_interface uv run python -m runtimes     # API under /api/dataspace-wallet-interface
uv run pytest -q tests/test_c4_m2_*.py
```

## Links

- Spec: [README](../../spec/C4-M2-DataspaceWalletInterface/README.md),
  [openapi.yaml](../../spec/C4-M2-DataspaceWalletInterface/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)

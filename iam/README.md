<!--
Copyright (c) 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Test Portal IAM (C2-M5)

C2-M5 ready to use for the hackathon: Keycloak with the realm of the spec, the test persons of `testdata/` and a stand-in for the EBW-Connector, so that teams can work without wallets. Test values only, not for operation. Keys, secrets and passwords are public on purpose.

```text
realm-osp.json                 realm file for operation, the only source
test/
  build-test-realm.py          builds test/import/ from realm-osp.json and the test objects
  test-objects.hackathon.json  variant hackathon: OSP A and OSP B, persons from testdata/
  test-objects.json            variant test: for the tests of C2-M5, Erika and Max are bound
  import/                      generated realm files, one folder per variant (hackathon, test; wallet, both and password are built on demand)
  keys/, jwks/, .env.test      test keys and secrets
  get-token.py                 gets a token
  check-hackathon.py           start state of the variant hackathon
  check-acceptance.py          acceptance cases of C2-M5 section 13 (variant test)
```

## Start

From the root of the repository:

```bash
docker compose up -d
```

Keycloak answers after about a minute at `http://localhost:8080/auth`. `demo.py` sets `IAM_URL` and `IAM_REALM` for each installation, and stops with a hint if Keycloak does not answer yet. To run an installation yourself, set them as in the table.

| | OSP A | OSP B |
|---|---|---|
| `IAM_URL` | `http://localhost:8080/auth` | `http://localhost:8080/auth` |
| `IAM_REALM` | `CX-Central` | `CX-Central-B` |
| Issuer | `…/realms/CX-Central` | `…/realms/CX-Central-B` |
| UI | `http://localhost:3000` | `http://localhost:3001` |
| Client at the stand-in | `portal-iam` | `portal-iam-b` |

One Keycloak with two realms keeps it light enough for a laptop. Tokens of the two OSPs differ in `iss`, so an OSP refuses the tokens of the other one. An account belongs to one realm, so its ID differs per OSP.

For a clean Keycloak, remove the container with `docker compose down`. The variant for the tests of C2-M5:

```bash
IAM_VARIANT=test docker compose up -d
```

## Sign-in methods: wallet, password or both

The variants above sign in at the stand-in `TEST-EBW`. With `--sign-in` the script builds one more variant without the stand-in. It is the variant hackathon (OSP A and OSP B, persons from `testdata/`) with the sign-in methods of the value, and its folder has the name of the value:

| `--sign-in` | Sign-in | Who can sign in |
|---|---|---|
| `wallet` | The Portal IAM redirects to the EBW-Connector at once, as `realm-osp.json` describes it. | Persons with a wallet. |
| `both` | The sign-in page of the Portal IAM: a form for name and password and the button "EUDI-Wallet". | The test persons with their password, everybody else with a wallet. |
| `password` | The sign-in page with the form only. No EBW-Connector is needed. | The test persons with their password. |

```bash
uv run python iam/test/build-test-realm.py --sign-in both --ebw-connector-url http://localhost:8077
```

`wallet` and `both` need `--ebw-connector-url`, for example the EBW-Connector in `ebw/`. The realm files contain that address, so these variants are built on demand and not committed. The script writes:

- `test/import/<value>/`: the realms of OSP A and OSP B. There is no realm `TEST-EBW`.
- `test/import/<value>.ebw-clients.json` (not for `password`): the Portal IAM of each OSP as a client of the EBW-Connector (`portal-iam`, `portal-iam-b`: JWKS and redirect URI of its realm, scopes `openid profile`). Add these entries to the `CLIENTS_FILE` of the EBW-Connector. A `CLIENTS_FILE` replaces the two clients the EBW-Connector registers by default, so keep those in the file if you use the demo portal or the Business Wallet.

Start Keycloak with `IAM_VARIANT=<value>`, on a clean Keycloak.

What the value changes in the realm:

| | `wallet` | `both` | `password` |
|---|---|---|---|
| Browser flow | `browser-ebw`: redirect to the identity provider | `browser` of Keycloak: sign-in page | `browser` of Keycloak: sign-in page |
| Identity provider `ebw-connector` | enabled | enabled | disabled |
| Test persons | no password | password | password |

**Password.** A test person signs in with the `key` of `testdata/` as the name (`otto`, `rolf`, `pia`, ...) and the password `TEST_EBW_PASSWORD` of `test/.env.test`. The password is typed only on the sign-in page of the Portal IAM; the direct grant stays denied in every variant. Nobody can register an account with a password and nobody can reset one: the accounts with a password are the test persons. The portal UI must not preselect the identity provider: start the BFF without `BFF_IDP_HINT`, otherwise Keycloak skips its sign-in page.

**Wallet.** A person who signs in with a wallet gets a new account with the portal role `Applicant`, as on a first sign-in in operation. The `sub` of the EBW-Connector is derived from the person data and the client, so the same person gets the same account at every sign-in. This account is not the account of a test person with the same name: Erika Mustermann from a wallet and the test person `erika` are two accounts.

**Address of the EBW-Connector.** It has to be the same for everyone who uses it: the browser (redirect), Keycloak (token request, JWKS) and the EBW-Connector itself (its `PUBLIC_URL`, which is the issuer and the audience of the client assertion). The EBW-Connector in turn fetches the JWKS of the realm at `http://localhost:8080/auth/…`. With everything on one host without Docker, `http://localhost:8077` or the tunnel address of `ebw/tools/start.py --tunnel` works. With Keycloak in a container, use a public address of the EBW-Connector. When the address changes (a new tunnel), set `issuer`, `authorizationUrl`, `tokenUrl` and `jwksUrl` of the identity provider `ebw-connector` again, through the Admin API or with a clean Keycloak.

**What differs from the variant hackathon.**

- The test persons keep their link to the stand-in in the realm file, although the stand-in is missing: `tools.keycloak_admin.reset_realm` recognises the persons by it. In the variant `wallet` they cannot sign in.
- Every start of an installation with test tools restores the start state of the realm (see "Start state"): accounts created by a sign-in with a wallet are deleted then. Keep the installation running during a demo. (`TEST_TOOLS=false` leaves the realm untouched, but it also leaves out every other test tool of the installation.)
- `check-hackathon.py` and `get-token.py` for persons do not apply; tokens of service accounts work as before.
- The verification attestation of the registration is a separate setting: the installation trusts the EBW-Connector only if `ATTESTATION_ISSUER`, `ATTESTATION_JWKS_URL` and `ATTESTATION_CLIENT_IDS` point at it (C1-M2 README 4). `config/osp-*/module-config.json` points at the test double of `tools/ebw_signer.py`; the process environment wins.

Checked on 2026-11-23 with Keycloak 26.8.1 and the EBW-Connector of `ebw/` on one host, variants `wallet` and `both`: sign-in through the portal UI with a wallet (first and second sign-in of a person, a second person) and with a password; registration with a verification attestation of the EBW-Connector, submission, pre-check of the review with every check passed, approval by a reviewer who signed in with a password, and the applicant bound to the new company as `Company Admin`. The variant `password` was built, not run.

## Test persons

From `testdata/persons-osp-a.json` and `testdata/persons-osp-b.json`; `sub` in the token is the `id` there. Every account also has the portal role `Applicant`. At the stand-in `TEST-EBW` the name is the `key`, the password is in `test/.env.test`. Nina (`nina`) has no account yet: her first sign-in creates it.

## Tokens

```bash
uv run python iam/test/get-token.py erika
```

```bash
uv run python iam/test/get-token.py gerd --realm CX-Central-B
```

```bash
uv run python iam/test/get-token.py svc-c3-m1
```

A token of a test person comes from the real browser flow: Portal IAM, redirect to the stand-in, form, back. After a binding, the next sign-in returns the new roles.

## Service accounts

- `svc-<module>` for every module of the spec (`portal_common.spec.modules()`), with every step and query permission and the secret `SERVICE_CLIENT_SECRET` (`tokens.service_token`).
- `svc-c2-m2` and `svc-c2-m3` also have their rights on the Admin API (C2-M5 5.9), so teams of C2-M2 and C2-M3 build against the real interface.
- `sa-csp`, `sa-csp-issuer`, `sa-csp-wallet` sign in with `private_key_jwt` against the JWKS of the CSP stand-in. Keycloak in the container reaches the stand-in on the host at `host.docker.internal:8100`.

## Start state

Every start of an installation with `IAM_URL` restores the start state of its realm from `iamRealmFile` of its settings, like every other module in memory: `/scaffold/reset` does the same. Accounts get their attributes and portal roles from the file, further accounts and clients are deleted. The realm and its keys stay. With `TEST_TOOLS=false` the realm is never touched. The admin account of the test installation is in `test/.env.test`; `KEYCLOAK_ADMIN_USER` and `KEYCLOAK_ADMIN_PASSWORD` replace it.

## Checks

On a fresh start of the variant hackathon:

```bash
uv run python iam/test/check-hackathon.py
```

On a fresh start of the variant test:

```bash
uv run python iam/test/check-acceptance.py
```

Not automated: case 19 needs the seeding job of the portal releases, case 22 a real wallet.

## Changing the realm

Change `realm-osp.json`, run `uv run python iam/test/build-test-realm.py`, and start with a clean Keycloak. The script reads the list of modules from `spec/`. Values per OSP are placeholders `${NAME}` as in C2-M5 section 4. The service accounts of `CALLBACK_CLIENTS` have one placeholder each: `CALLBACK_JWKS_URL_SA_CREDENTIAL_ISSUER`, `CALLBACK_CLIENT_SECRET_SA_IH_CALLBACK`, `CALLBACK_CLIENT_SECRET_SA_DIV_CALLBACK`.

## Where this differs from C2-M5 version 0.2

To be taken over by the spec:

1. **5.3:** RSA key with 4096 bit. Keycloak 25 does not accept 3072.
2. **5.9:** `svc-c2-m2` and `svc-c2-m3` have their rights on `realm-management` also in their own scope mapping. With `fullScopeAllowed: false` they are otherwise missing from the token.
3. **13 case 7:** Keycloak takes over an `email` claim on the first login, and no setting prevents it. `check-acceptance.py` checks `company_id` and `bpn` and prints a note on the email. The EBW-Connector delivers no email, so accounts stay without one in operation.
4. **14:** realm files named `<realm>-realm.json`, the variant hackathon with OSP B, `svc-<module>`, persons from `testdata/`.

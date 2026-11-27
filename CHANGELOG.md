# Changelog

All notable changes to this project will be documented in this file.
See also the overarching [Eclipse Tractus-X changelog](https://eclipse-tractusx.github.io/changelog) for the Tractus-X releases.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Combined OpenAPI 3.1.0 document of the installation in `docs/api/openAPI.yaml` and `.tractusx` metadata configuration for the Tractus-X API hub (TRG 1.08, TRG 2.05).
- Repository set-up according to the [Tractus-X Release Guidelines](https://eclipse-tractusx.github.io/docs/release): legal documentation, `.tractusx` metadata file, contribution templates, Dependabot and security scans (CodeQL, KICS, Trivy, TruffleHog), container build and documentation structure ([dataspace-mgm-ui#1](https://github.com/eclipse-tractusx/dataspace-mgm-ui/issues/1))
- Eclipse Dash IP check aligned with tractusx-testlab: `dependencies.yml` only checks, the new `dependencies-update.yml` regenerates `DEPENDENCIES` daily, requests IP reviews (secret `DASH_GITLAB_API_TOKEN`) and opens a pull request.
- IP checks and TRG workflows completed: `dependencies-update.yml` reads the IP Lab links Dash prints as `/-/work_items/<n>`, keeps one issue with the IP Lab requests open while a dependency is restricted (TRG 7.04) and starts the Eclipse Dash IP Check on its own pull request; the Dash check, CodeQL, KICS, TruffleHog, Trivy and the image build also run for pull requests into `develop`; the new `license-headers.yml` checks the headers of added files (TRG 7.02).
- Hackathon scaffold: all modules of the spec mounted as stand-ins, Process Orchestration (C12-M1), test Portal IAM (Keycloak), EBW stack for tests with a real wallet, `demo.py` and the setup check `check.py`.
- Event inbox `POST /api/v1/events/inbox` (FRAMEWORK 6, OP-54): receives the CloudEvents of split-out modules in structured or binary content mode, with the token of the service account of the publishing module, and delivers each `source` and `id` once. First controller of the new `controllers/` package: one folder per API category and version, as in the Industry Core Hub backend.
- Feature-first layout and runtimes made of features ([ADR-0003](docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)): the onboarding modules C1-M2 and C3-M1 and the technical users C2-M3 move from `modules/` to `features/registration/`, `features/company_profile/` and `features/technical_user/` (`controllers/` with one folder per API path segment, `services/`, `managers/`, `models/`, `router.py`, `main.py`, index), without changing their API; `runtimes/` builds hybrid (`onboarding`) or single-feature runtimes, selected in the image with `RUNTIME`; `MODULE_URLS` accepts readable feature names.
- The application review C1-M3 moves from `modules/c1_m3/` to `features/application_review/` (ADR-0003): controllers per path segment, the pre-check and the review cases in `services/`, the neighbour client, configuration and repository in `managers/`, pydantic models and SQLModel tables (`review_case`, `audit_log`, own database, in-memory SQLite without a URL) in `models/`, and a `README.md`. Review case responses no longer carry the internal field `changedAt`, which the spec does not define.
- C4-M1 Credentials moves from `modules/c4_m1/` to `features/credentials/` (ADR-0003): controllers per API path segment, the rules and the issuer route choice with the built-in stand-in issuer in `services/`, the credential store and the issuer clients in `managers/`; pydantic models of the API in `models/credentials.py` and the tables of README 5 as SQLModel tables in the feature's own database (`CREDENTIALS_DATABASE_URL`, `C4_M1_DATABASE_URL`, `DATABASE_URL`, else in-memory SQLite).
- C3-M2 CSP Connection moves from `modules/c3_m2/` to `features/csp_connection/` in the same layout (ADR-0003), with its own pydantic models on `portal_common.models`, a README, and its tables as SQLModel classes in its own database (`portal_common.database`) instead of in-memory dicts.
- C11-M1 Notifications moves from `modules/c11_m1/` to `features/notifications/` (ADR-0003): the inbox operations in `controllers/notifications/`, rules, event engine, closing, recipients and inbox logic in `services/`, the store, the background worker with its retry policy, the neighbour client and the stand-in data of C2-M2 in `managers/`, the rule type, the pydantic models of the API and the SQLModel tables of README 5 in `models/`; the inbox is stored in the feature's own database (`NOTIFICATIONS_DATABASE_URL`, in-memory SQLite without one).
- The connectors C6-M1 move from `modules/c6_m1/` to `features/connector/` in the feature-first layout of ADR-0003 (`controllers/` per API path segment, `services/`, `managers/` with the repository, the neighbour client and the stand-in data in `managers/data/`, `models/` with pydantic models and SQLModel tables in its own database).
- C4-M2 Dataspace Wallet Interface migrated to `features/dataspace_wallet_interface/` (ADR-0003): the provider adapters (SAP DIV, IdentityHub, CSP) move to `managers/providers/`, store, encryption and DID resolution to `managers/`, the wallet and account logic to `services/`, the SAP DIV callbacks and every other operation to `controllers/`; its state moves from the in-memory store to SQLModel tables in its own database (`models/tables.py`) and its API models to pydantic (`models/api.py`).
- Subscriptions C10-M1 move from `modules/c10_m1/` to `features/subscriptions/` (feature-first layout, ADR-0003).
- Folder rules of a feature in `features/AGENTS.md` (F1 to F14) and the skill `feature-architecture` (`feature-check.py`), which checks them statically; `tests/test_feature_architecture.py` runs it on every feature. The company profile's `config.py` and stand-in data move to `managers/`, the Problem factories of the technical users to `models/errors.py`.
- Shared pydantic bases for the models of every feature in `portal_common.models` (`ApiModel`, `RequestBody`, `StepRequest`, `StepResult`, `Page`, `Uuid`, `Bpnl`, `CountryCode`); `portal_common.database`, one SQLAlchemy/SQLModel database per feature (`<FEATURE>_DATABASE_URL`, then `<SPEC_ID>_DATABASE_URL`, then `DATABASE_URL`, else in-memory SQLite; new dependency `sqlmodel`); the feature rules F15 (a `README.md` that names the migrated module and explains the feature), F16 (own pydantic models in `models/`) and F17 (SQLModel tables in `models/tables.py`) in `features/AGENTS.md` and `feature-check.py`.
- Process Orchestration (C12-M1) moves from `modules/c12_m1/` to `features/process_orchestration/` (ADR-0003): the engine is split into `services/` (flow execution, step dispatch) and `managers/` (process store, flow catalogue, neighbour calls), with pydantic models of the API and SQLModel tables for processes, step runs, delivered events and the retrigger audit; it still reaches every module by spec id through `portal_common.layout` and `neighbours`.
- Users and App Access C2-M2 moves from `modules/c2_m2/` to `features/app_access/` (feature-first layout, ADR-0003): the Java-style layers (`c2_m2_api`, `c2_m2_impl`, `c2_m2_rs_api`, `c2_m2_rs_service`) become `models/`, `services/`, `managers/` and a controller tree checked by `mount()` against the spec; the vendored public/private OpenAPI split and the standalone `main.py` are replaced by the spec's `openapi.yaml` and `features/app_access/main.py` (`RUNTIME=app_access`). `C2_M2_DATABASE_URL` stays the database variable.
- One runtime per module ([ADR-0002](docs/architecture/decisions/ADR-0002-runtime-per-module.md)): `ENABLED_FEATURES` starts the same image with only some modules, `EVENT_SINKS` forwards published events to the other runtimes' event inbox (retries, off the request path), the Helm chart renders one Deployment and Service per runtime (`runtimes`), and `docker-compose.poc.yml` runs the registration and the company profile as two pods (`deploy/poc/poc_check.py`).
- Process Orchestration (C12-M1) as the event hub of a split installation ([ADR-0006](docs/architecture/decisions/ADR-0006-process-orchestration-as-event-hub.md)): every runtime forwards the CloudEvents it publishes to the event inbox of the runtime of C12-M1, found with the neighbour address rule (`C12_M1_URL`, `MODULE_URLS`), without `EVENT_SINKS`; the feature's `on_event` routes each event on to the runtimes of the subscribing features (`services/event_hub.py`, `managers/event_routes.py`) before running its flows. `EVENT_SINKS` still adds inboxes, the forwarder never posts to its own `BASE_URL`, and the relay also remembers the events it published, so a copy that comes back is not delivered twice. The inbox contract and `events.publish` do not change.
- Cloud-native domain clusters and automated PostgreSQL database provisioning ([ADR-0005](docs/architecture/decisions/ADR-0005-cloud-native-database-provisioning-and-domain-clusters.md)): domain runtimes in `runtimes/` (`security`, `marketplace`, `connectivity`, `operations`), automated database initialization scripts in `deploy/postgres/` (`init-feature-databases.sh`, `init-feature-databases.sql`), dedicated PostgreSQL 16 compose environment (`docker-compose.domain-clusters.yml`), comprehensive reverse proxy routing in `deploy/poc/gateway.conf`, and ratcheted quality gate baseline.
- Helm chart support for PostgreSQL persistence (TRG 3.02, TRG 5.06) and ADR-0005 domain clusters deployment profile: added `database` configuration in `charts/dataspace-mgm/values.yaml` and `templates/_helpers.tpl`, dedicated `charts/dataspace-mgm/values-domain-clusters.yaml` preconfiguring the 5 domain clusters with TRG 5.04-compliant resource limits, runtime health test pods in `charts/dataspace-mgm/templates/tests/test-runtimes.yaml` (TRG 5.09), bumped chart version to 0.2.0, and updated `helm-test.yml` CI workflow for develop.

### Changed

- Update `DEPENDENCIES` with newly approved Eclipse Dash reviews for `click` (#32995), `fastapi` (#32978), and `uvicorn` (#32984) (TRG 7.04).

- **Breaking:** the migrated features are served under readable paths instead of their spec ids: `/api/registration`
  (was `/api/c1-m2`), `/api/company-profile` (was `/api/c3-m1`) and `/api/technical-user` (was `/api/c2-m3`); the old
  paths answer 404. Problem types, event
  sources, permissions and service accounts keep the spec id. Concept for one database per feature in a shared
  PostgreSQL instance ([ADR-0003](docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)).
- **Breaking:** C2-M2 Users and App Access is served under `/api/app-access` (was `/api/c2-m2`); the old path answers
  404. Problem types, events, permissions and `svc-c2-m2` keep the spec id.
- **Breaking:** the application review C1-M3 is served under `/api/application-review` (was `/api/c1-m3`); the old path answers 404. Problem types, events, permissions and `svc-c1-m3` keep the spec id.
- **Breaking:** C4-M1 Credentials is served under `/api/credentials` (was `/api/c4-m1`); the old path answers 404, and the callback address given to the issuers is `/api/credentials/issuer-callbacks/{credentialKind}`. Problem types, event sources, permissions and `svc-c4-m1` keep the spec id.
- **Breaking:** C8-M1 Offers moves from `modules/c8_m1/` to `features/offers/` (ADR-0003) and is served under `/api/offers` (was `/api/c8-m1`); the old path answers 404. Problem types, event sources, permissions and `svc-c8-m1` keep the spec id.
- **Breaking:** C3-M2 CSP Connection is served under `/api/csp-connection` (was `/api/c3-m2`); the old path answers
  404, and the CSP stand-in calls back `/api/csp-connection/csp-notifications`. Problem types, events, permissions
  and `svc-c3-m2` keep the spec id.
- **Breaking:** C11-M1 Notifications is served under `/api/notifications` (was `/api/c11-m1`); the old path answers
  404. Problem types, events, permissions and `svc-c11-m1` keep the spec id.
- **Breaking:** the connectors C6-M1 are served under `/api/connector` (was `/api/c6-m1`); the old path answers 404.
  Problem types, events, permissions and `svc-c6-m1` keep the spec id.
- **Breaking:** C4-M2 Dataspace Wallet Interface is served under `/api/dataspace-wallet-interface` (was `/api/c4-m2`,
  also for the SAP DIV callbacks); the old path answers 404. Problem types, events, permissions and `svc-c4-m2` keep the spec id.
- **Breaking:** C10-M1 Subscriptions is served under `/api/subscriptions` (was `/api/c10-m1`); the old path answers 404.
- Outgoing HTTP calls of `portal_common.http` use one pooled client (keep-alive).
- **Breaking:** Process Orchestration (C12-M1) is served under `/api/process-orchestration` (was `/api/c12-m1`); the old path answers 404. Problem types, events, permissions and `svc-c12-m1` keep the spec id.
- The company profile keeps its state in SQLModel tables on `portal_common.database` instead of the memory and the hand-written PostgreSQL transport: it also reads `COMPANY_PROFILE_DATABASE_URL` (before `C3_M1_DATABASE_URL` and `DATABASE_URL`), uses the `pg8000` driver instead of `psycopg`, and no longer answers `501 not-implemented` for a missing driver. Its responses are pydantic models; list endpoints refuse `page < 0` and `size` outside 1 to 100 with 400.

- Events are CloudEvents 1.0 (`specversion`, `id`, `source` `urn:<module>`, `type`, `time`, `datacontenttype`, `data`) as proposed in the spec (FRAMEWORK 6, OP-54): `events.publish(module, type, data)`; the flat form `events.publish({"eventType": ...})` is deprecated; consumers read the content from `event["data"]`.

### Fixed

- Startup database persistence: preserve existing feature database records on application startup instead of emptying tables; table reset remains available via explicit scaffold reset and test fixtures ([#101](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/101)).
- Enforce database isolation in multi-feature runtimes: refuse startup when plain `DATABASE_URL` is set without dedicated variables for each served feature, preventing table collisions across features (ADR-0003 decision 6, FRAMEWORK 4.9, [#102](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/102)). Updated Helm chart to automatically derive dedicated feature database URLs when persistence is enabled.
- C11-M1 Notifications serves its operations with the `operationId` of its spec (`listNotifications`, `getNotification`, …) instead of names FastAPI generated from the paths; `docs/api/openAPI.yaml` is exported again (#106).
- Quality gate: guard `modules/` directory discovery in `checks.py` when all legacy modules are fully migrated to `features/`.

- C11-M1 Notifications gives `doneAt` in UTC (FRAMEWORK 4.1) also when the closing event's `time` has another offset (#103).
- The spec loader takes the module id from the spec folder (`C3-M1-CompanyProfile` -> `c3-m1`) instead of the `servers` URL, so the spec's readable base paths (`/api/company-profile`, FRAMEWORK 4.1, OP-55 of portal-backend-spec) load as well as the old `/api/c3-m1`.
- Align the Docker build and runtime images with the project's required Python 3.12 version.
- Every module of an installation reads its own database variable (`C2_M2_DATABASE_URL`, `C3_M1_DATABASE_URL`); `DATABASE_URL` stays the fallback for a module that runs alone. Before, one `DATABASE_URL` switched C2-M2 and C3-M1 to the same database ([#54](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/54)).
- standin.router(): accept custom tags via optional `tags` parameter ([#51](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/51)).

[Unreleased]: https://github.com/eclipse-tractusx/dataspace-mgm-service/commits/main

# Changelog

All notable changes to this project will be documented in this file.
See also the overarching [Eclipse Tractus-X changelog](https://eclipse-tractusx.github.io/changelog) for the Tractus-X releases.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository set-up according to the [Tractus-X Release Guidelines](https://eclipse-tractusx.github.io/docs/release): legal documentation, `.tractusx` metadata file, contribution templates, Dependabot and security scans (CodeQL, KICS, Trivy, TruffleHog), container build and documentation structure ([dataspace-mgm-ui#1](https://github.com/eclipse-tractusx/dataspace-mgm-ui/issues/1))
- Eclipse Dash IP check aligned with tractusx-testlab: `dependencies.yml` only checks, the new `dependencies-update.yml` regenerates `DEPENDENCIES` daily, requests IP reviews (secret `DASH_GITLAB_API_TOKEN`) and opens a pull request.
- Hackathon scaffold: all modules of the spec mounted as stand-ins, Process Orchestration (C12-M1), test Portal IAM (Keycloak), EBW stack for tests with a real wallet, `demo.py` and the setup check `check.py`.
- Event inbox `POST /api/v1/events/inbox` (FRAMEWORK 6, OP-54): receives the CloudEvents of split-out modules in structured or binary content mode, with the token of the service account of the publishing module, and delivers each `source` and `id` once. First controller of the new `controllers/` package: one folder per API category and version, as in the Industry Core Hub backend.
- Feature-first layout and runtimes made of features ([ADR-0003](docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)): the onboarding modules C1-M2 and C3-M1 move from `modules/` to `features/registration/` and `features/company_profile/` (`controllers/` with one folder per API path segment, `services/`, `managers/`, `models/`, `router.py`, `main.py`, index), without changing their API; `runtimes/` builds hybrid (`onboarding`) or single-feature runtimes, selected in the image with `RUNTIME`; `MODULE_URLS` accepts readable feature names.
- One runtime per module ([ADR-0002](docs/architecture/decisions/ADR-0002-runtime-per-module.md)): `ENABLED_FEATURES` starts the same image with only some modules, `EVENT_SINKS` forwards published events to the other runtimes' event inbox (retries, off the request path), the Helm chart renders one Deployment and Service per runtime (`runtimes`), and `docker-compose.poc.yml` runs the registration and the company profile as two pods (`deploy/poc/poc_check.py`).

### Changed

- **Breaking:** the migrated features are served under readable paths instead of their spec ids: `/api/registration`
  (was `/api/c1-m2`) and `/api/company-profile` (was `/api/c3-m1`); the old paths answer 404. Problem types, event
  sources, permissions and service accounts keep the spec id. Concept for one database per feature in a shared
  PostgreSQL instance ([ADR-0003](docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)).
- Outgoing HTTP calls of `portal_common.http` use one pooled client (keep-alive).

- Events are CloudEvents 1.0 (`specversion`, `id`, `source` `urn:<module>`, `type`, `time`, `datacontenttype`, `data`) as proposed in the spec (FRAMEWORK 6, OP-54): `events.publish(module, type, data)`; the flat form `events.publish({"eventType": ...})` is deprecated; consumers read the content from `event["data"]`.

### Fixed

- Align the Docker build and runtime images with the project's required Python 3.12 version.

[Unreleased]: https://github.com/eclipse-tractusx/dataspace-mgm-service/commits/main

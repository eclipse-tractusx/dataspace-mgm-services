# ADR-0004: Internal boundaries, layer architecture, and quality gate

**Status:** proposed (16 Nov 2026), Refs #54, amends [ADR-0003](ADR-0003-feature-first-layout-and-runtimes.md), resolves review findings on [#63](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/63).  
**Builds on:** [ADR-0002](ADR-0002-runtime-per-module.md) (one image, many runtimes), [ADR-0003](ADR-0003-feature-first-layout-and-runtimes.md) (feature-first layout), and the quality gate proposal of [#54](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/54).

---

## Context

The hackathon implementation successfully delivered functional modules conforming to external OpenAPI specifications and `AGENTS.md` call conventions. However, the internal implementation of modules grew organically without shared conventions:
- File sizes expanded significantly (e.g. C1-M2 `interface.py` with 829 lines, C3-M1 `interface.py` with 1281 lines).
- Business logic, HTTP routing, database access, and neighbour coordination were often intermixed in single files.
- While [#68](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/68) successfully established automated CI for unit tests (`pytest`) and acceptance scenarios (`demo.py`), the codebase lacked static analysis, type checking, architectural boundary verification, and automated OpenAPI contract parity.
- [ADR-0003](ADR-0003-feature-first-layout-and-runtimes.md) proposed a feature-first architecture (`features/<feature>/`) inspired by the Eclipse Tractus-X Industry Core Hub, but concrete amendments and formal layer boundary rules are required before it can be uniformly applied across all modules.

To ensure long-term maintainability for both human contributors and autonomous AI coding agents, we require **explicit layer boundary rules** and **one deterministic quality gate** with an automated ratchet mechanism.

---

## Amendments to ADR-0003

To resolve the architectural discrepancies identified during review of [#50](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/50) and [#63](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/63), this ADR formally establishes the following amendments to ADR-0003:

### 1. Readable API Paths & Migration Boundary
* **Migrated Features (`features/<name>/`):** Served exclusively under their readable endpoint path (`/api/registration`, `/api/company-profile`, `/api/technical-users`). Legacy `/api/<module>` endpoints return HTTP 404 once migrated.
* **Legacy Modules (`modules/<id>/`):** Remain mounted under `/api/<module>` until their respective migration PR is merged.
* **Frontend Alignment:** The UI (`packages/core-http`) transitions endpoint mappings per migrated feature slice.

### 2. Isolated Database Environment Variables
* Each migrated feature reads its own database connection via `<FEATURE>_DATABASE_URL` (e.g. `REGISTRATION_DATABASE_URL`, `COMPANY_PROFILE_DATABASE_URL`, `TECHNICAL_USERS_DATABASE_URL`).
* Fallback to the monolith `DATABASE_URL` is permitted only when executing single-feature standalone runtimes or in test environments.

### 3. Layer Boundary & Call Hierarchy
Requests flow strictly top-down within a feature slice:
```text
HTTP Request
     │
     ▼
[controllers/]           (HTTP routes, request parsing, response formatting)
     │
     ▼
[interface.py]           (Public contract: steps, queries, in-process API)
     │
     ▼
[services/]              (Domain rules, business logic, transaction boundaries)
     │
     ▼
[managers/]              (Repositories, DAO persistence backends, neighbour clients)
```
* **Routers and Controllers:** Must NOT import persistence repositories (`managers/`) or external neighbour gateways directly. All business operations are delegated to `services/` or `interface.py`.
* **Cross-Feature Communication:** When Feature A calls Feature B in-process, it MUST call Feature B's `interface.py` only (`AGENTS.md` Convention 5). Direct cross-feature imports of controllers, services, or managers are strictly prohibited.

### 4. Scope of AST Layer Enforcement
* The strict layer rules (`FORBIDDEN` import table) are enforced specifically within `features/`.
* Legacy code under `modules/` is protected by `tests/test_interfaces.py` and the baseline ratchet to prevent breaking unclassified legacy files while they await migration.

### 5. OpenAPI Security Scheme Declaration
* `portal_common` shall declare an OpenAPI HTTP Bearer security scheme rather than taking raw `Header(authorization)`. This ensures that generated OpenAPI documents match the upstream specification without injecting unprompted parameter entries.

---

## Decision

### 1. The Unified Quality Gate
A single script serves as the gatekeeper for all contributors and automated agents:
```bash
uv run python tools/quality/gate.py
```
The quality gate executes locally, in pre-commit hooks, and in GitHub Actions CI (`.github/workflows/tests.yml`).

### 2. Core Quality Checks

| Check | Tool / Engine | Purpose |
|---|---|---|
| `ruff` | `ruff check` | Linting, syntax validation, style consistency, and `ANN401` (banning untyped `Any` in function signatures). |
| `mypy` | `mypy` | Static type checking configured via `pyproject.toml`. |
| `layers` | AST Inspector (`tools/quality/layers.py`) | Enforces import directionality between controllers, services, and managers in `features/`. |
| `neighbours` | AST Inspector | Outgoing neighbour calls via `portal_common.neighbours` must reside exclusively within `managers/neighbour_client.py` (or legacy `gateways.py`). |
| `problems` | AST Inspector | Construction of `Problem(...)` instances is restricted to `errors.py`. |
| `contract` | Schema Comparator (`tools/quality/http_layer.py`) | Compares generated FastAPI OpenAPI against `spec/<module>/openapi.yaml`. Priority route matching ensures literal paths (e.g. `/notifications/count`) take precedence over parameterized templates (`/notifications/{notificationId}`). |

### 3. The Ratchet Mechanism (`baseline.json`)
Existing violations across legacy modules are documented in `tools/quality/baseline.json`:
* The gate **FAILS** if any check exceeds its documented baseline count, preventing new technical debt.
* When a refactor or feature migration resolves existing violations, `baseline.json` is lowered, permanently locking in the improved quality baseline.

---

## Alternatives Considered

| Option | Reason for Rejection |
|---|---|
| Enforce strict layer rules on `modules/` immediately | Fails immediately on 220+ legacy files. The ratchet allows progressive cleanup as modules migrate to `features/`. |
| Run linter and type checker only in CI | Developers and agents discover failures only after pushing commits. Local execution matches CI 1:1. |
| Hardcode rules directly into arc42 chapters | Arc42 chapters describe the running architecture. Normative decisions belong in versioned ADRs. |

---

## Consequences

- Maintainers, contributors, and AI coding agents operate under the exact same verification standard.
- Feature migrations can proceed cleanly one module at a time without breaking overall repository health.
- Upstream `develop` remains continuously green and protected against contract drift and architectural erosion.

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-services/blob/main/docs/architecture/decisions/ADR-0004-internal-boundaries-and-quality-gate.md

# ADR-0003: Feature-first layout and runtimes made of features

**Status:** proposed (9 Nov 2026, updated 13 Nov 2026), proof of concept with the onboarding: the features `registration` (C1-M2) and
`company_profile` (C3-M1), migrated from the hackathon folders `modules/c1_m2/` and `modules/c3_m1/`.
**Builds on:** [ADR-0002](ADR-0002-runtime-per-module.md) (one image, many runtimes), the call convention of
`AGENTS.md`, and the layered backend of the Eclipse Tractus-X Industry Core Hub (`controllers/`, `services/`,
`managers/`, `models/`, `runtimes/`).

## Context

The hackathon scaffold gives every spec module one folder `modules/<id>/` with two files that grew large:
`interface.py` (C1-M2: 829 lines, C3-M1: 1281) holds state, validation, business rules, steps and queries;
`router.py` holds every HTTP route. The names say nothing to a newcomer (`c1_m2`, `c3_m1`), HTTP and business logic
are mixed, and the only deployable unit was the whole installation (ADR-0002 added module selection by id).

We want a professional structure that people can read and maintain, that keeps the contract of the spec, and that
lets us choose per environment which features run together in one pod and which run alone. The Industry Core Hub
layers are the reference: controllers per feature, services shared by several controllers, managers for state and
adapters, models, and runtimes that assemble the app.

## Decision

1. **One package per feature, the same shape everywhere** (`features/__init__.py`):

   ```text
   features/<feature>/
       __init__.py      index: NAME, MODULE (spec id), lifecycle hooks reset(), on_startup(), on_event()
       router.py        `router = mount(controllers, MODULE)`: the controller tree under the base path
       main.py          the feature as its own runtime
       interface.py     in-process contract (call convention): steps and queries for other features and C12
       controllers/     HTTP only, one folder per path segment of the API; `controller.py` per folder
       services/        business logic, shared by the controllers and by interface.py; no HTTP
       managers/        state and adapters: repositories, storage backends, clients of neighbours
       models/          value sets and data models of the API (when the feature has its own)
   ```

   The layers of the Industry Core Hub stay. They are cut **per feature (vertical slice)**, not per layer across the
   repository, so one feature is one folder. One team owns it, reviews and tests it, and can deploy it alone.
2. **Readable names, also in the API.** The feature name is the readable part of the spec folder
   (`C1-M2-Registration` -> `registration`, `ModuleSpec.name`), and the files are named after what they do
   (`application_service.py`, `company_repository.py`, `document_service.py`). The API of a feature carries the same
   name instead of the spec id: `/api/registration` instead of `/api/c1-m2`, `/api/company-profile` instead of
   `/api/c3-m1` (`_` as `-`).
   - One rule, one place: `portal_common.layout.base_path(module)`, read through `ModuleSpec.base_path`. Routers,
     stand-ins, neighbour calls and Process Orchestration's HTTP calls all follow it; the spec's own path stays
     readable as `ModuleSpec.spec_path`. A module switches the moment its feature package exists; until then it
     keeps `/api/<module>`.
   - Hard switch: a feature does not serve its old path (404). The UI (`dataspace-mgm-ui`) and its vendored
     `openapi.yaml` copies follow.
   - FRAMEWORK 4.1 calls `/api/<module>` provisional ("until the common path convention is settled"); this is the
     convention we propose for it, recorded in each feature's `OPEN-QUESTIONS.md`.
   - Identifiers that are not addresses keep the spec id for now: Problem types (`urn:c1-m2:problem:*`), event
     `source`, permissions, service accounts (`svc-c1-m2`, clients in the Keycloak realm). Renaming them touches the
     realm and the UI's error handling and is a separate decision.
3. **Controllers mirror the URL.** `controllers/` is the base path of the feature, and every sub-folder is one path
   segment (`_` for `-`), so the tree reads like the API:

   ```text
   controllers/                        /api/registration
       applications/                   /applications              ITEM = "applicationId"
           controller.py               "", "/{applicationId}", "/{applicationId}/submit", ...
           documents/controller.py     /applications/{applicationId}/documents: "", "/{documentId}"
       osp/applications/controller.py  /osp/applications
       steps/controller.py             /steps: "/complete-application", "/close-application"
   ```

   A `controller.py` declares `controller = Controller("<tag>")` and its operations with a path relative to the
   folder: `""`, `"/{item}"`, `"/action"` or `"/{item}/action"`; anything deeper is a sub-folder. A folder whose
   sub-folders belong to one item names it once in `__init__.py` (`ITEM = "applicationId"`). No path is written
   twice: `portal_common.routing.mount()` builds the full paths, refuses an operation that is not in the
   module's `openapi.yaml`, an action that is also a sub-folder and a folder without `__init__.py`, and binds the
   permission of the spec operation (`x-permission`) to the parameter `claims: dict = Permission`. The rules are
   tested in `tests/test_routing.py`.
4. **Dependency direction.** `controllers -> services -> managers`; `models` is used by all of them; `interface.py`
   re-exports service functions. Another feature, Process Orchestration and a not-yet-migrated module import only
   `features.<name>.interface`; `tests/test_interfaces.py` enforces this for `features/` and `modules/` alike.
   The shared building blocks of controllers (`Controller`, `Permission`, `mount`, paging, `download`) are in
   `portal_common.routing`.
5. **Runtimes are made of features** (`runtimes/`):
   - `runtimes/installation.py`: every module, the modular monolith (the default);
   - `runtimes/onboarding.py`: a **hybrid** runtime, `create_runtime(registration, company_profile)`;
   - `features/<feature>/main.py`: one feature alone;
   - one image serves all of them: `RUNTIME=<runtime or feature> python -m runtimes` (Dockerfile `CMD`). The
     installation runtime still takes `ENABLED_FEATURES` (readable names or spec ids) for modules without a
     runtime of their own.

   A split runtime calls its own features in-process (`<MODULE>_URL=in-process`) and every other module over HTTP
   with the service token (`MODULE_URLS`, which also accepts readable keys such as `{"company_profile": "..."}`),
   events go through the event inbox (ADR-0002).
6. **One database per feature, one PostgreSQL instance.** FRAMEWORK 1 asks for an own database and an own database
   user per module, and that no module reads or writes another module's database. We keep that boundary without
   running one server per feature:
   - **Instance:** one PostgreSQL instance (cluster) per installation. Inside it, one **database** per feature, named
     after the feature (`registration`, `company_profile`) and owned by a login role of the same name.
     `REVOKE CONNECT ON DATABASE <feature> FROM PUBLIC` lets each role connect to its own database only.
   - **Databases, not schemas:** PostgreSQL cannot join or reference across databases. "References to other modules
     only by ID" is then enforced by the server, not by convention or grants.
   - **Connection per feature:** a feature reads its own variable `<FEATURE>_DATABASE_URL`
     (`REGISTRATION_DATABASE_URL`, `COMPANY_PROFILE_DATABASE_URL`) at call time (AGENTS.md 6), resolved in one place
     (`portal_common.database.url(module)`).
     - The spec's plain `DATABASE_URL` (README 4) is accepted only by a runtime that serves exactly one feature.
     - A hybrid runtime with only `DATABASE_URL` refuses to start, because its features would silently share one
       database.
   - **Credentials:** one Kubernetes Secret per feature. A pod mounts only the Secrets of the features it serves; a
     hybrid pod gets one per feature. Credentials never appear in logs, events or step results (FRAMEWORK 4.6).
   - **Schema ownership:** each feature owns its tables and migrations in `managers/`, with the version table in its
     own database. They are applied at start with its own role; no feature runs DDL in another database.
   - **Provisioning:** an idempotent Helm hook Job, or the operator of a managed PostgreSQL, creates role and
     database per feature (`CREATE ROLE company_profile LOGIN ...`, `CREATE DATABASE company_profile OWNER
     company_profile`). Only this job holds the admin credential.
   - **Operations:** one instance to run, monitor and back up. One feature can be restored alone
     (`pg_dump -d <feature>`). Each feature has its own connection pool per pod, so the sum of replicas × pool size
     stays below `max_connections` (PgBouncer when it does not). A feature that outgrows the shared instance moves to
     its own with dump and restore plus a new URL, without a code change.
   - **State of the PoC:**
     - `company_profile` has a PostgreSQL transport (`managers/postgres_backend.py`) that still reads the plain
       `DATABASE_URL`;
     - `registration` keeps its data in memory;
     - C2-M2 (not migrated) also reads the plain `DATABASE_URL`, so in today's monolith both would share one
       database.

     Next steps: `portal_common.database`, the per-feature variable in `company_repository`, the Helm Secrets and
     provisioning job, and a PostgreSQL service in the compose PoC.
7. **Discovery instead of registration.** `portal_common.layout` finds a feature by its readable name
   (`features/<name>/` exists), so migrating a module needs no central list. `scaffold.registry` mounts it as kind
   `feature`, and every operation of the spec that the feature does not implement still answers from the
   spec-driven fallback.
8. **Step by step.** A spec module without a feature package keeps running from `modules/<id>/` unchanged. Migrating
   one more module means:
   1. create `features/<name>/` with the shape above, moving the code with `git mv` so its history stays;
   2. split `interface.py` into services and managers, and `router.py` into one controller folder per path
      segment, without changing behaviour;
   3. repoint the module's tests;
   4. delete `modules/<id>/`;
   5. announce the new base path `/api/<feature>` to the UI and other callers; the ingress follows from the Helm
      values;
   6. when the module has a database: provision `<feature>` in the shared instance and set
      `<FEATURE>_DATABASE_URL`.

## Alternatives

| Option | Why not |
|---|---|
| Layer-first as in the Industry Core Hub (`controllers/<category>/v1/`, `services/<category>/<name>/`, `managers/...`, `models/...` at the top) | Tried first in this PR. One feature is spread over four trees, so a change touches four folders, ownership and CODEOWNERS get blurred, and no folder can be deployed or reviewed on its own. The ICH layers stay inside each feature. |
| Keep `modules/<id>/` and only split the files | Keeps the unreadable names; the folder still mixes HTTP and business logic by convention only. |
| Select runtimes only by environment (`ENABLED_MODULES`, ADR-0002) | Works, but which features run together is then deployment knowledge, not code. Runtimes in code are reviewed, tested (`tests/test_runtime_split.py`) and run the same locally, in compose and in Helm. The variable remains for modules that are not migrated. |
| Keep `/api/<module>` for every module (FRAMEWORK 4.1 as written) | Leaves the unreadable id in every URL the UI, operators and logs see; the spec itself marks it provisional. |
| Serve both the old and the readable path for a while | Doubles every route, the Swagger documentation and the ingress rules, and hides callers that never migrate; with one UI and Process Orchestration in the same repository, a hard switch is cheaper. |
| One schema per feature in one shared database | Cross-schema joins and foreign keys stay possible, so the module boundary depends on grants alone and one wrong `GRANT` breaks it; the spec asks for an own database. |
| One PostgreSQL instance per feature | Strongest isolation, but multiplies servers, backups, monitoring and cost for a handful of small databases. Stays possible per feature later, by changing its URL only. |
| One shared database for all features | Violates FRAMEWORK 1 (own database per module) and couples every schema migration to every team. |
| One repository or image per feature | Multiplies pipelines and Eclipse Dash runs for the same dependencies; nothing differs per feature yet (ADR-0002). |

## Consequences

- People find the same thing in the same place in every feature; the onboarding PoC turns two 829- and
  1281-line files into services, managers and controllers named after what they do, and the largest file is
  now the PostgreSQL backend (600 lines).
- The team rule of `AGENTS.md` extends to features: after migration, a team works in `features/<name>/` instead of
  `modules/<id>/`. Test files keep their spec-id names (`tests/test_c1_m2_*.py`) so the definition of done is
  unchanged.
- Hybrid or single runtimes are a deployment choice (`RUNTIME`, Helm `runtimes.items[].runtime`); moving a feature
  between pods changes no code.
- FastAPI decides at route creation which parameters come from the path, and keeps included routers lazy while the
  spec fallback reads `router.routes`. So `mount()` creates every route once with its full path instead of
  nesting routers with prefixes.
- Swagger tags are set per controller, so several folders can share one tag (`Registration: Applications`).
- URLs say what they serve (`/api/company-profile/companies/{companyId}`). The UI and every external caller must
  switch to the readable paths of a feature when it migrates; the ingress and the PoC gateway route
  `/api/<feature>` and `/api/<module>` side by side meanwhile.
- One PostgreSQL instance keeps operations simple while the server keeps the features' data apart. A noisy feature
  can still slow down the shared instance; moving it to its own instance is a configuration change.
- Until every module is migrated, two layouts coexist; `portal_common.layout` hides this from the registry, the
  stand-ins and the call convention.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-services/blob/main/docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md

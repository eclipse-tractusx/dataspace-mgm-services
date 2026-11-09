# ADR-0003: Feature-first layout and runtimes made of features

**Status:** proposed (9 Nov 2026), proof of concept with the onboarding: the features `registration` (C1-M2) and
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
2. **Readable names.** The feature name is the readable part of the spec folder (`C1-M2-Registration` ->
   `registration`, `ModuleSpec.name`), and the files are named after what they do (`application_service.py`,
   `company_repository.py`, `document_service.py`). The spec id stays only where the contract defines it: paths
   (`/api/c1-m2`), Problem types (`urn:c1-m2:problem:*`), event sources, service accounts (`svc-c1-m2`).
3. **Controllers mirror the URL.** `controllers/` is the base path of the spec, and every sub-folder is one path
   segment (`_` for `-`), so the tree reads like the API:

   ```text
   controllers/                        /api/c1-m2
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
6. **Discovery instead of registration.** `portal_common.layout` finds a feature by its readable name
   (`features/<name>/` exists), so migrating a module needs no central list. `scaffold.registry` mounts it as kind
   `feature`, and every operation of the spec that the feature does not implement still answers from the
   spec-driven fallback.
7. **Step by step.** A spec module without a feature package keeps running from `modules/<id>/` unchanged. Migrating
   one more module means:
   1. create `features/<name>/` with the shape above, moving the code with `git mv` so its history stays;
   2. split `interface.py` into services and managers, and `router.py` into one controller folder per path
      segment, without changing behaviour;
   3. repoint the module's tests;
   4. delete `modules/<id>/`.

## Alternatives

| Option | Why not |
|---|---|
| Layer-first as in the Industry Core Hub (`controllers/<category>/v1/`, `services/<category>/<name>/`, `managers/...`, `models/...` at the top) | Tried first in this PR. One feature is spread over four trees, so a change touches four folders, ownership and CODEOWNERS get blurred, and no folder can be deployed or reviewed on its own. The ICH layers stay inside each feature. |
| Keep `modules/<id>/` and only split the files | Keeps the unreadable names; the folder still mixes HTTP and business logic by convention only. |
| Select runtimes only by environment (`ENABLED_MODULES`, ADR-0002) | Works, but which features run together is then deployment knowledge, not code. Runtimes in code are reviewed, tested (`tests/test_runtime_split.py`) and run the same locally, in compose and in Helm. The variable remains for modules that are not migrated. |
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
- Until every module is migrated, two layouts coexist; `portal_common.layout` hides this from the registry, the
  stand-ins and the call convention.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-services/blob/main/docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md

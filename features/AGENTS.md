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

# Instructions for coding agents: features

These rules apply to everything under `features/`, on top of the root [`AGENTS.md`](../AGENTS.md). A feature is a
spec module migrated to the feature-first layout of
[ADR-0003](../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md). Every feature has the
same shape, so code is always found in the same place. Check that with the skill
[`feature-architecture`](../.claude/skills/feature-architecture/SKILL.md) before you push:

```bash
.claude/skills/feature-architecture/scripts/feature-check.py <feature> --strict
```

Each rule below has an id (F1 to F17). The checker reports findings with the same id. The test
`tests/test_feature_architecture.py` runs the checker on every feature in CI.

## The shape (F1 to F6)

```
features/<feature>/
    __init__.py         index: NAME, MODULE, reset(), optional on_startup() and on_event(event); nothing else
    router.py           router = mount(controllers, MODULE)
    main.py             the feature as its own runtime: create_runtime(<feature>)
    interface.py        in-process contract: the steps and queries of the spec (call convention)
    README.md           migrated from which module, what the feature does, how it works (F15)
    OPEN-QUESTIONS.md   open points against the spec
    controllers/        HTTP only, one folder per path segment
    services/           business logic, no HTTP
    managers/           state and adapters: repositories, storage backends, neighbour clients, configuration
        data/           data files of the feature (stand-in data, seeds), bare file names count from here
    models/             pydantic models of requests, steps and responses, value sets, Problem factories (F16)
```

- **F1, name.** The folder name is the readable name of the spec folder in snake case: `C2-M3-TechnicalUser` gives
  `technical_user`, `C3-M1-CompanyProfile` gives `company_profile`. Do not use a plural or a team name. The API is
  served under that name with `-` (`/api/technical-user`). The package declares `MODULE = "<spec id>"` once.
- **F2, required entries.** Every file and package of the tree above exists (`README.md` and `models/` are
  checked by F15 and F16). `managers/data/` is
  only needed when the feature has data files.
- **F3, nothing else at the top level.** Configuration and data files go to `managers/`. Shared values and Problem
  factories go to `services/` or `models/`.
- **F4, index.** `NAME` is the folder name and `MODULE` the spec id. The index defines only the lifecycle hooks and
  does not import `router.py`, so importing a feature does not build its routes.
- **F5, router.** `router.py` holds the single line `router = mount(controllers, MODULE)` (`portal_common.routing`).
  `mount()` checks every operation against the module's `openapi.yaml` and binds its `x-permission`. Do not
  write an `APIRouter` by hand.
- **F6, main.** `main.py` calls `create_runtime(<feature>)` from `runtimes/`.

## Controllers (F7)

- One folder per path segment, in snake case (`company_roles/` serves `/company-roles`). Every folder has an
  `__init__.py`, otherwise `mount()` refuses the tree.
- A sub-resource of one item: the parent's `__init__.py` names that item once (`ITEM = "companyId"`), so
  `companies/technical_users/` serves `/companies/{companyId}/technical-users`.
- A folder holds only `__init__.py` and `controller.py`. Helpers go to `services/`.
- `controller = Controller("<Feature title>: <group>")`, and the operations are declared on it with paths relative to
  the folder: `""`, `"/{item}"`, `"/action"` or `"/{item}/action"`. A deeper path needs a sub-folder.
- An operation's parameter `claims: dict = Permission` receives the checked token. The controller applies the scope
  (`company_scope(MODULE, claims, companyId)`), calls one service or interface function and returns its result.
  It holds no business logic.

## Layers and imports (F8, F9)

- **F8.** Dependencies only go downwards: controllers, then services, then managers. `models/` can be imported from
  any layer. `fastapi` and `starlette` are imported only in `controllers/`, because services and managers are also
  called in-process by Process Orchestration and by other features.
- **F9.** Another feature or module is imported only through its interface: `features.<name>.interface` or
  `modules.<id>.interface`. A migrated module is never imported from its old `modules/<id>/` path. Calls that may
  cross a pod boundary go through `portal_common.neighbours` (with the module's `<ID>_URL` or `MODULE_URLS`).

## Configuration, migration, tests, headers (F10 to F14)

- **F10.** The environment is read in a manager (`managers/config.py`), at call time and never at import (root
  `AGENTS.md` rule 6). Services ask that manager. This rule is advisory (low).
- **F11.** When a module is migrated, its `modules/<id>/` folder is removed. Keep no compatibility adapters: other
  modules reach it through `portal_common.layout` and `neighbours`.
- **F12.** The tests of the feature are in `tests/test_<id>_*.py`, named after the spec id.
- **F13.** Every file has the license header of the repository, with the AI disclosure and an `Assisted-By:` line
  when AI wrote it.
- **F14.** The code has no literal `/api/<spec id>`. A feature reads its base path from `spec.module(MODULE).base_path`
  or uses paths relative to it. Problem types (`urn:<id>:problem:...`), event sources, permissions and service
  accounts (`svc-<id>`) keep the spec id.

## README and models (F15, F16)

- **F15, README.** `features/<feature>/README.md` starts with the title and the spec id, names the module it was
  migrated from (`modules/<id>/`) and has the sections `## What it does` (purpose, callers) and `## How it works`
  (flows and states, folder map, interface, events, configuration, persistence, how to run and test it alone).
  It describes only what the code does.
- **F16, models.** A feature defines its own models with pydantic v2 in `models/`: request bodies, step inputs,
  responses and value sets, with the field names of its `openapi.yaml` in JSON. Controllers declare them as body and
  `response_model`; services take and return them. The shared bases are in `portal_common.models`:
  - `ApiModel` (snake_case in Python, camelCase in JSON, `to_json()`), `RequestBody` (unknown fields and explicit
    `null` refused), `StepRequest` (`processId`, `stepRunId`), `StepResult[T]` (`done()`, `running()`),
    `Page[T]` (`Page.of(rows, page, size)`);
  - the formats `Uuid`, `Bpnl`, `CountryCode`.

  A feature never imports another feature's models: it calls the other feature's `interface.py` and validates the
  answer with its own model.

## Database (F17)

- **F17, tables.** A feature with persistent state keeps it in its own database through SQLAlchemy, with SQLModel
  tables (the approach of the Industry Core Hub backend), and `portal_common.database`:
  - the tables are SQLModel classes in `models/tables.py` on the feature's own base,
    `Table = database.table_base(MODULE)`, so they sit in the feature's own `MetaData` and only in its database;
  - a row is a pydantic model: convert it to the API model with `Model.model_validate(row, from_attributes=True)`,
    and put fields that row and API model share in one SQLModel base without `table=True`;
  - repositories in `managers/` are the only code that opens `database.session(MODULE)`; services call them;
  - the index creates the tables in `on_startup()` (`database.create_tables(MODULE)`) and `reset()` empties them
    (`database.reset_tables(MODULE)`);
  - the URL is `<FEATURE>_DATABASE_URL`, then `<SPEC_ID>_DATABASE_URL`, then `DATABASE_URL`; without one the feature
    runs on a private in-memory SQLite database, so tests and `demo.py` need no server;
  - no hand-written SQL strings and no dict stores next to the tables; indexes on the columns the feature looks up by.

  The checker does not test F17; reviewers do.

## Shared code and reuse

- Code used by two or more features goes to `portal_common/` as a small module with one purpose and its own test
  (`tests/test_portal_common_*.py`), not into one feature for the others to import. Code used by one feature stays
  in that feature.
- A feature contains only what it needs to run alone as its own runtime (`main.py`). It holds no code of another
  feature and no leftovers of `modules/<id>/`.
- Keep the work per request small: look objects up by key (a `dict` by id) instead of scanning lists, make one
  neighbour call for a batch instead of one per item, and page before you build response models.

## Migrating one more module

1. `git mv modules/<id>/... features/<name>/...` into the shape above, so the history stays.
2. Write the controllers as a tree of path segments. The interface keeps its convention names.
3. Remove `modules/<id>/` and point the tests at `features.<name>`, with the API under `/api/<name with ->`.
4. Add the feature to the lists in the root `AGENTS.md`, `docs/api/README.md`, `CHANGELOG.md` (breaking: new base
   path) and ADR-0003, and add a row for the base path to `OPEN-QUESTIONS.md`.
5. Write `README.md` (F15), the pydantic models (F16) and the SQLModel tables (F17).
6. `feature-check.py <name> --strict`, `uv run pytest -q`, `uv run python demo.py --small-iam`.

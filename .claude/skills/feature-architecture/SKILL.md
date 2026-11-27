---
name: feature-architecture
description: Check that a feature under features/ of the Dataspace Management Service follows the feature-first folder architecture of ADR-0003 and features/AGENTS.md, statically - folder name from the spec, the required index/router/main/interface/controllers/services/managers, controllers as a tree of path segments with Controller and relative paths, layers controllers -> services -> managers without HTTP below controllers, imports of other modules only through their interface, no leftover modules/<id>/, tests, license headers, no literal /api/<spec id>. Use while developing or migrating a feature, for "does my feature follow the architecture", "where does this file go", "is the migration of C2-M3 complete", or before pushing a feature branch.
---

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

# Feature architecture

A migrated module is a feature package `features/<name>/` with one fixed shape
([ADR-0003](../../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)). The binding rules
are in [`features/AGENTS.md`](../../../features/AGENTS.md), F1 to F17. This skill checks them without importing or
running anything, so it also works on a feature that does not start yet.

```bash
C=.claude/skills/feature-architecture/scripts/feature-check.py
$C                          # every feature: one summary line, then the findings
$C technical_user           # one feature, by folder name ...
$C c2-m3                    # ... or by spec id
$C technical_user --strict  # exit 1 on a blocker or high finding (pre-push hook, CI)
$C --json                   # findings as JSON (feature, rule, severity, file, message)
```

## Procedure

1. **Before writing code** for a feature, read `features/AGENTS.md` and an existing feature of the same kind
   (`features/registration/` for a feature with its own models, `features/company_profile/` for one with a database
   backend, `features/technical_user/` for one with an IAM adapter).
2. **Place every new file** by its responsibility: an HTTP operation goes to `controllers/<segment>/controller.py`,
   logic to `services/`, state, configuration and clients to `managers/`, value sets and Problem factories to
   `models/`. If a file fits nowhere, it is probably two files.
3. **Run the checker** after each change to the tree and fix every `blocker` and `high` finding. `medium` findings
   are fixed before the PR. `low` findings (F10, tag prefixes) are advice: fix them when you touch the file anyway.
4. **Prove the behaviour**: the checker cannot see behaviour. `mount()` enforces the spec at start-up
   (`uv run pytest -q tests/test_routing.py`), then `uv run pytest -q` and `uv run python demo.py --small-iam`.
5. **In a review**, put the checker output for the feature in the PR description, next to `merge-guard`.

## Findings

| Rule | Severity | What it means | Fix |
|---|---|---|---|
| F1 | blocker | folder name is not the readable name of the spec folder, or no `MODULE` | rename the folder (`git mv`) to the name the finding gives |
| F2 | high | a required file or package is missing | create it like in the other features |
| F3 | medium | an extra file at the top level | move it to `managers/` (config, data) or `services/` / `models/` |
| F4 | high / low / medium | index without `NAME`, `MODULE` or `reset()`; other functions; imports the router | keep only the lifecycle hooks in `__init__.py` |
| F5 | high / medium | `router.py` is not `router = mount(controllers, MODULE)` | delete the hand-written routes, declare them in controllers |
| F6 | high | `main.py` without `create_runtime(...)` | copy `main.py` of another feature |
| F7 | blocker / high / medium / low | controller tree: missing `__init__.py`, folder name, extra files, `APIRouter`, a path deeper than one segment, tag | one folder per segment, `Controller("<Title>: <group>")`, relative paths |
| F8 | high | wrong layer direction, or `fastapi` below `controllers/` | move the code to the right layer, return data instead of responses |
| F9 | blocker / high | import of another module's internals, or of a migrated module's old `modules/<id>/` path | import `features.<name>.interface` / `modules.<id>.interface` |
| F10 | low | the environment is read outside `managers/` | read it in `managers/config.py` at call time |
| F11 | high | `modules/<id>/` still exists for a migrated module | remove it, with no adapters |
| F12 | medium | no `tests/test_<id>_*.py` | add the feature's tests |
| F13 | medium / low | no license header, or AI disclosure without `Assisted-By:` | copy the header of a neighbouring file |
| F14 | medium | literal `/api/<spec id>` in the code | `spec.module(MODULE).base_path` or a relative path |
| F15 | medium | no `README.md`, or it does not name `modules/<id>/` or lacks `## What it does` / `## How it works` | write the README of the feature |
| F16 | medium | no `models/` package, or no pydantic model in it | define the feature's models on `portal_common.models` |

## Requirements

`python3` 3.10+ and nothing else (standard library only). The spec (`spec/` or `SPEC_DIR`) is needed for F1. Without it,
the folder name is not checked and the checker says so. `FEATURE_CHECK_ROOT` points the checker at another
checkout. `tests/test_feature_architecture.py` runs it on the repository (`--strict` must pass) and on a broken
fixture that has to trip every rule.

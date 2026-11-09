#################################################################################
#  Copyright (c) 2026 Contributors to the Eclipse Foundation
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  This program and the accompanying materials are made available under the
#  terms of the Apache License, Version 2.0 which is available at
#  https://www.apache.org/licenses/LICENSE-2.0.
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""Module registry: every module of the spec, either a migrated feature `features/<name>/` (ADR-0003,
located by `portal_common.layout`) or its hackathon folder `modules/<module id with _>/`.

A feature brings its `router.py` and the lifecycle hooks of its index (`reset()`, optional
`on_startup()` and `on_event(event)`); its kind is "feature".

Contract of a module folder (a team replaces only its folder):
- `interface.py` with a function for every step and query of the spec (README, module structure);
- `router.py` with `router` (an `APIRouter` under the base path of the spec) and `reset()`;
- optional in `router.py`: `on_event(event)` (subscriber of the event relay), `on_startup()`;
- `STANDIN = True` marks the stand-in, `PROVIDED = True` a provided module (C12-M1); a team's
  module sets neither;
- an empty `__init__.py`, no top-level modules beside the folders.

The list of modules comes from the spec (every folder with an `/api/<module>` base), limited to
the features of the runtime (`runtimes/`, `ENABLED_FEATURES`; ADR-0002, ADR-0003). A module
without a folder is still mounted, as the spec-driven fallback (every path answers 501, steps DONE).
Every operation of the spec that a module does not implement is added from the fallback too.
"""
from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Iterable
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace

from portal_common import layout, runtime, spec

LAST = ("c11-m1", "c12-m1")   # subscribers that react to the events of all others


@dataclass
class Entry:
    id: str
    module: ModuleType | SimpleNamespace | None   # router + lifecycle, None = spec fallback only
    kind: str                   # "feature", "stand-in", "provided", "team" or "fallback"


def _feature(mid: str) -> SimpleNamespace:
    index = layout.index(mid)
    if index.MODULE != mid:
        raise ValueError(f"features.{index.NAME} declares MODULE {index.MODULE!r}, the spec folder says {mid!r}")
    hooks = {k: getattr(index, k) for k in ("reset", "on_startup", "on_event") if hasattr(index, k)}
    return SimpleNamespace(router=layout.router(mid), **hooks)


def load(features: Iterable[str] | None = None) -> list[Entry]:
    """The modules of this process: `features` (readable names or spec ids), else `ENABLED_FEATURES`, else all."""
    enabled = runtime.enabled_modules(features)
    entries = []
    for mid in spec.modules():
        if enabled is not None and mid not in enabled:
            continue   # served by another runtime, reached through MODULE_URLS
        if layout.feature(mid):
            entries.append(Entry(mid, _feature(mid), "feature"))
            continue
        name = f"modules.{mid.replace('-', '_')}.router"
        mod = importlib.import_module(name) if importlib.util.find_spec(name.rsplit(".", 1)[0]) and \
            importlib.util.find_spec(name) else None
        kind = ("fallback" if mod is None else "stand-in" if getattr(mod, "STANDIN", False)
                else "provided" if getattr(mod, "PROVIDED", False) else "team")
        entries.append(Entry(mid, mod, kind))
    return sorted(entries, key=lambda e: (e.id in LAST, LAST.index(e.id) if e.id in LAST else 0, e.id))

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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Where the code of a spec module lives (ADR-0003).

A migrated module is a feature package `features/<name>/` (layout in `features/__init__.py`); its
name is the readable name of the spec folder (`C1-M2-Registration` -> `registration`), and so is its
API (`/api/registration`, `base_path()`). A module without a feature package still runs from its
hackathon folder `modules/<id>/` under the spec's `/api/<module>`. Migrating one more module means
creating its feature package; nothing here changes.
"""
from __future__ import annotations

import importlib
import importlib.util
from functools import cache
from types import ModuleType

from . import spec


@cache
def feature(module: str) -> str | None:
    """Readable name of the module's feature package, or None while it is still in `modules/`."""
    name = spec.module(module).name
    return name if importlib.util.find_spec(f"features.{name}") else None


def base_path(module: str) -> str:
    """Base path of the module's API: a feature is served under its readable name (`registration` ->
    `/api/registration`, `company_profile` -> `/api/company-profile`), a module in `modules/` under the
    spec's `/api/<module>` until it migrates. The old spec path is not served for a feature."""
    name = feature(module)
    return f"/api/{name.replace('_', '-')}" if name else spec.module(module).spec_path


def features() -> dict[str, str]:
    """Spec id -> feature name of every migrated module."""
    return {mid: name for mid in spec.modules() if (name := feature(mid))}


def interface_package(module: str) -> str:
    """Dotted name of the module's `interface.py`, wherever it lives."""
    name = feature(module)
    return f"features.{name}.interface" if name else f"modules.{module.replace('-', '_')}.interface"


def index(module: str) -> ModuleType:
    """The feature's index: `NAME`, `MODULE`, `reset()` and optional `on_startup()` / `on_event(event)`."""
    name = feature(module)
    if name is None:
        raise LookupError(f"{module} has no feature package")
    return importlib.import_module(f"features.{name}")


def router(module: str):
    """The HTTP API of a feature (`features/<name>/router.py`)."""
    index(module)
    return importlib.import_module(f"features.{feature(module)}.router").router

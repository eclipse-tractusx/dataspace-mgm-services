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
"""Call convention between modules: every module has `interface.py` with a function for every step
and query of its openapi.yaml, and modules import each other only through that interface, wherever
the module lives (`modules/<id>/` or, once migrated, `features/<name>/`, ADR-0003)."""
import ast
import importlib
from pathlib import Path

import pytest

from portal_common import layout, spec

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mid", sorted(spec.modules()))
def test_interface_exposes_every_step_and_query(mid):
    ms = spec.module(mid)
    iface = importlib.import_module(layout.interface_package(mid))
    ops = [op for op in ms.operations if op.is_step or op.is_query]
    names = [op.function_name for op in ops]
    assert len(names) == len(set(names)), f"{mid}: two operations with the same function name"
    missing = [f"{op.method} {op.path} -> {op.function_name}" for op in ops
               if not callable(getattr(iface, op.function_name, None))]
    assert not missing, f"{layout.interface_package(mid)} lacks: {missing}"


def test_function_names_follow_the_convention():
    c1_m2 = spec.module("c1-m2")
    assert c1_m2.find("GET", "/internal/applications/a1").function_name == "get_application_internal"
    assert c1_m2.find("POST", "/steps/complete-application").function_name == "complete_application"
    assert spec.snake_case("getBPNForCompany") == "get_bpn_for_company"


def _owners() -> dict[str, str]:
    """Package prefix -> spec module that owns the code under it."""
    owners = {f"modules.{mid.replace('-', '_')}": mid for mid in spec.modules()}
    owners |= {f"features.{name}": mid for mid, name in layout.features().items()}
    return owners


def _owner(dotted: str, owners: dict[str, str]) -> str | None:
    parts = dotted.split(".")
    for n in range(len(parts), 0, -1):
        if ".".join(parts[:n]) in owners:
            return owners[".".join(parts[:n])]
    return None


def _imported_names(source: str, package: str):
    """Full dotted name of everything a file of the package `package` imports."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:   # relative: resolve against the package of the file
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1] + ([base] if base else []))
            yield from (f"{base}.{a.name}" for a in node.names)


def _foreign(source: str, package: str, owners: dict[str, str] | None = None) -> list[str]:
    """Imports of another module's code that do not go through its interface."""
    owners = owners or _owners()
    me = _owner(package, owners)
    interfaces = {layout.interface_package(mid) for mid in spec.modules()}
    wrong = []
    for name in _imported_names(source, package):
        other = _owner(name, owners)
        if other is None and name.split(".")[0] in ("modules", "features") and len(name.split(".")) == 2:
            other = "?"   # `from modules import c1_m2`: a whole package of another module
        if other and other != me and not any(name == i or name.startswith(i + ".") for i in interfaces):
            wrong.append(name)
    return wrong


def test_import_check_itself():
    ok = "from modules.c10_m1.interface import list_subscriptions\nfrom ..c10_m1 import interface\n" \
         "import modules.c10_m1.interface\nfrom . import router\n" \
         "from features.registration.interface import get_application_internal"
    assert _foreign(ok, "modules.c3_m2") == []
    own = "from features.company_profile import company_service\n" \
          "from features.company_profile.managers import company_repository\nfrom . import shared"
    assert _foreign(own, "features.company_profile") == []
    bad = "from modules.c10_m1 import router\nfrom modules.c10_m1.router import x\nfrom ..c10_m1.service import y\n" \
          "from modules import c10_m1\nimport modules.c10_m1\n" \
          "from features.registration import application_service\n" \
          "from features.registration.managers import application_repository\n" \
          "from modules.c1_m2.interface import get_application_internal"   # migrated: stale path
    assert len(_foreign(bad, "modules.c3_m2")) == 8


def _code_files():
    for top in ("modules", "features"):
        for file in sorted((ROOT / top).glob("*/**/*.py")):
            yield file, ".".join(file.relative_to(ROOT).with_suffix("").parts[:-1])


def test_modules_import_each_other_only_through_interface():
    wrong = []
    for file, package in _code_files():
        wrong += [f"{file.relative_to(ROOT)}: {n}" for n in _foreign(file.read_text(encoding="utf-8"), package)]
    assert not wrong, "import other modules only from their interface: " + "; ".join(wrong)

#!/usr/bin/env python3
#################################################################################
#  Copyright (c) 2026 Catena-X Automotive Network e.V.
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
"""Check that a feature package follows the feature-first layout of ADR-0003, statically (nothing is imported or run).

Usage: feature-check.py [feature ...] [--strict] [--json]

  (no feature)  every package under `features/`
  <feature>     a feature by its folder name (`technical_user`), its spec id (`c2-m3`) or its path
  --strict      exit 1 when a finding is a blocker or high (pre-push hook, CI)
  --json        the findings as JSON, one object per finding

The rules are the ones of `features/AGENTS.md` (F1 to F16); each finding names its rule, the file and how to fix it.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.dont_write_bytecode = True  # keep the repository free of __pycache__

# the repository; FEATURE_CHECK_ROOT points it at another checkout (or a fixture in the tests)
ROOT = Path(os.environ.get("FEATURE_CHECK_ROOT") or Path(__file__).resolve().parents[4]).resolve()
FEATURES = ROOT / "features"
MODULES = ROOT / "modules"
SEVERITIES = ("blocker", "high", "medium", "low")

REQUIRED_FILES = ("__init__.py", "router.py", "main.py", "interface.py", "OPEN-QUESTIONS.md")
REQUIRED_DIRS = ("controllers", "services", "managers")
OPTIONAL = {"models", "README.md", "__pycache__"}
LIFECYCLE = {"reset", "on_startup", "on_event"}
RELATIVE_PATH = re.compile(r"(/\{\w+\})?(/[a-z0-9]+(-[a-z0-9]+)*)?")
METHODS = {"get", "post", "put", "patch", "delete"}
ENV_READ = re.compile(r"\bos\.(environ|getenv)\b")
# layer -> packages of the same feature it must not import (controllers -> services -> managers, ADR-0003)
FORBIDDEN_LAYERS = {
    "controllers": {"managers"},
    "services": {"controllers"},
    "managers": {"services", "controllers"},
    "models": {"services", "managers", "controllers"},
}
NO_HTTP = {"services", "managers", "models"}   # fastapi / starlette belong in controllers/ only


@dataclass
class Finding:
    feature: str
    rule: str
    severity: str
    file: str
    message: str


def snake_case(name: str) -> str:
    """Same rule as portal_common.spec.snake_case: `CompanyProfile` -> `company_profile`."""
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    return name.replace("-", "_").lower()


def spec_dir() -> Path | None:
    """The backend spec the scaffold reads (`SPEC_DIR`, else `spec/`); None when it is not there."""
    for candidate in (os.environ.get("SPEC_DIR"), ROOT / "spec"):
        if candidate and Path(candidate).is_dir() and any(Path(candidate).glob("C*-M*-*")):
            return Path(candidate)
    return None


def spec_names() -> dict[str, str]:
    """Spec id -> readable feature name (`c3-m1` -> `company_profile`), from the folder names of the spec."""
    folder = spec_dir()
    if folder is None:
        return {}
    out = {}
    for d in folder.iterdir():
        m = re.match(r"C(\d+)-M(\d+)-(.+)$", d.name)
        if d.is_dir() and m:
            out[f"c{m.group(1)}-m{m.group(2)}"] = snake_case(m.group(3))
    return out


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return None


def package_of(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts[:-1])


def imports(tree: ast.Module, package: str):
    """(dotted name, line) of every import, relative ones resolved against the file's package."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[: len(parts) - node.level + 1] + ([base] if base else []))
            for a in node.names:
                yield f"{base}.{a.name}" if base else a.name, node.lineno


def module_literal(feature: Path) -> str | None:
    """The spec id the feature declares (`MODULE = "c2-m3"`), wherever in the package it is assigned."""
    for path in sorted(feature.rglob("*.py")):
        tree = parse(path)
        for node in ast.walk(tree) if tree else ():
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MODULE" for t in node.targets) \
                    and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return node.value.value
    return None


class Checker:
    def __init__(self, feature: Path, names: dict[str, str]):
        self.feature = feature
        self.name = feature.name
        self.names = names
        self.findings: list[Finding] = []
        self.module = module_literal(feature)

    def add(self, rule: str, severity: str, path: Path | str, message: str) -> None:
        file = rel(path) if isinstance(path, Path) else path
        self.findings.append(Finding(self.name, rule, severity, file, message))

    # ------------------------------------------------------------------ rules
    def run(self) -> list[Finding]:
        self.f1_name()
        self.f2_f3_shape()
        self.f4_index()
        self.f5_router()
        self.f6_main()
        self.f7_controllers()
        for path in sorted(self.feature.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = parse(path)
            if tree is None:
                self.add("F0", "blocker", path, "does not parse")
                continue
            self.f8_f9_imports(path, tree)
            self.f10_env(path)
            self.f13_header(path)
            self.f14_paths(path, tree)
        self.f11_old_folder()
        self.f12_tests()
        self.f15_readme()
        self.f16_models()
        return self.findings

    def f1_name(self) -> None:
        if self.module is None:
            self.add("F1", "blocker", self.feature, "no `MODULE = \"<spec id>\"` in the package; the index must export it")
            return
        expected = self.names.get(self.module)
        if not self.names:
            self.add("F1", "low", self.feature, "spec not found (`spec/` or SPEC_DIR): the folder name is not checked")
        elif expected is None:
            self.add("F1", "blocker", self.feature, f"MODULE {self.module!r} is not a module of the spec")
        elif expected != self.name:
            self.add("F1", "blocker", self.feature,
                     f"the folder of {self.module} must be `features/{expected}/` (readable name of the spec folder), "
                     f"not `features/{self.name}/`; its API is `/api/{expected.replace('_', '-')}`")

    def f2_f3_shape(self) -> None:
        for name in REQUIRED_FILES:
            if not (self.feature / name).is_file():
                self.add("F2", "high", self.feature / name, "missing: every feature has the same shape (features/AGENTS.md)")
        for name in REQUIRED_DIRS:
            if not (self.feature / name / "__init__.py").is_file():
                self.add("F2", "high", self.feature / name, "missing package (folder with `__init__.py`)")
        allowed = set(REQUIRED_FILES) | set(REQUIRED_DIRS) | OPTIONAL
        for entry in sorted(self.feature.iterdir()):
            if entry.name not in allowed:
                where = "managers/ (configuration, data files, adapters)" if entry.suffix in (".json", ".yaml", ".yml") \
                    or entry.stem in ("config", "settings") else "services/ (logic, shared values, Problem factories) " \
                    "or models/ (value sets, data models)"
                self.add("F3", "medium", entry, f"not part of the feature shape; move it to {where}")

    def f4_index(self) -> None:
        path = self.feature / "__init__.py"
        tree = parse(path) if path.is_file() else None
        if tree is None:
            return
        names, functions, exported = {}, set(), set()
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        names[t.id] = node.value
            elif isinstance(node, ast.FunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                exported |= {a.asname or a.name for a in node.names}
        name = names.get("NAME")
        if not (isinstance(name, ast.Constant) and name.value == self.name):
            self.add("F4", "high", path, f'the index assigns `NAME = "{self.name}"` (the folder name)')
        if "MODULE" not in names and "MODULE" not in exported:
            self.add("F4", "high", path, "the index exports `MODULE` (the spec id)")
        if "reset" not in functions and "reset" not in exported:
            self.add("F4", "high", path, "the index defines `reset()` (empty state; the runtime calls it at start and in tests)")
        for fn in sorted(functions - LIFECYCLE):
            if not fn.startswith("_"):
                self.add("F4", "low", path, f"`{fn}()` in the index: the index holds only the lifecycle hooks "
                                            "(reset, on_startup, on_event); logic belongs in services/")
        if any(n.endswith(".router") or n == "router" for n in exported):
            self.add("F4", "medium", path, "the index imports the router: the runtime loads `router.py` itself "
                                          "(importing it here builds every route on any import of the feature)")

    def f5_router(self) -> None:
        path = self.feature / "router.py"
        tree = parse(path) if path.is_file() else None
        if tree is None:
            return
        mounted = any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "router" for t in n.targets)
                      and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "mount"
                      for n in tree.body)
        if not mounted:
            self.add("F5", "high", path, "`router = mount(controllers, MODULE)` (portal_common.routing) builds the API "
                                         "from the controller tree; no hand-written APIRouter")
        for n in tree.body:
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                self.add("F5", "medium", path, f"`{n.name}` in router.py: hooks go in the index, logic in services/")

    def f6_main(self) -> None:
        path = self.feature / "main.py"
        if path.is_file() and "create_runtime(" not in path.read_text(encoding="utf-8"):
            self.add("F6", "high", path, "main.py builds the feature's own runtime with `create_runtime(<feature>)` "
                                         "(runtimes/)")

    def f7_controllers(self) -> None:
        root = self.feature / "controllers"
        if not root.is_dir():
            return
        tags = {}
        for d in sorted([root, *[p for p in root.rglob("*") if p.is_dir() and p.name != "__pycache__"]]):
            if not (d / "__init__.py").is_file():
                self.add("F7", "blocker", d, "folder without `__init__.py`: mount() refuses the controller tree")
            if d != root and not re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)*", d.name):
                self.add("F7", "high", d, "a controller folder is one path segment in snake_case (`company_roles` -> "
                                          "`/company-roles`)")
            for f in sorted(d.glob("*.py")):
                if f.name not in ("__init__.py", "controller.py") and d != root:
                    self.add("F7", "medium", f, "a controller folder holds only `__init__.py` and `controller.py`; "
                                                "helpers belong in services/, shared dependencies in portal_common")
                if d == root and f.name != "__init__.py":
                    self.add("F7", "medium", f, "`controllers/` itself is the base path: operations go in a sub-folder")
            controller = d / "controller.py"
            if controller.is_file():
                tags.update(self._controller(controller))
        prefixes = {t.split(":", 1)[0] for t in tags.values()}
        if len(prefixes) > 1:
            self.add("F7", "low", root, f"tags with different prefixes {sorted(prefixes)}: use `<Feature title>: <group>`")

    def _controller(self, path: Path) -> dict[str, str]:
        tree = parse(path)
        if tree is None:
            return {}
        source = path.read_text(encoding="utf-8")
        if "APIRouter" in source or "add_api_route" in source:
            self.add("F7", "high", path, "uses APIRouter/add_api_route: declare operations on "
                                         "`controller = Controller(...)` and let mount() build the routes")
        tag = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "controller" for t in node.targets) \
                    and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", None) == "Controller":
                arg = node.value.args[0] if node.value.args else None
                tag = arg.value if isinstance(arg, ast.Constant) else None
        if tag is None:
            self.add("F7", "high", path, "no `controller = Controller(\"<Feature title>: <group>\")`")
        if tag is not None and ":" not in tag:
            self.add("F7", "low", path, f"tag {tag!r}: use `<Feature title>: <group>`")
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr in METHODS and getattr(dec.func.value, "id", None) == "controller"):
                    continue
                arg = dec.args[0] if dec.args else None
                p = arg.value if isinstance(arg, ast.Constant) else ""
                if not RELATIVE_PATH.fullmatch(p):
                    self.add("F7", "high", f"{rel(path)}:{dec.lineno}",
                             f"path {p!r} of `{node.name}`: a path is '', '/{{item}}', '/action' or '/{{item}}/action' "
                             "relative to the folder; deeper paths belong in a sub-folder")
        return {rel(path): tag} if tag else {}

    def f8_f9_imports(self, path: Path, tree: ast.Module) -> None:
        own = f"features.{self.name}"
        parts = path.relative_to(self.feature).parts
        layer = parts[0] if len(parts) > 1 else None
        for name, line in imports(tree, package_of(path)):
            where = f"{rel(path)}:{line}"
            top = name.split(".")
            if layer in NO_HTTP and top[0] in ("fastapi", "starlette"):
                self.add("F8", "high", where, f"`{name}` in {layer}/: HTTP belongs in controllers/ (services and "
                                              "managers are called in-process too)")
            if name.startswith(own + "."):
                target = name[len(own) + 1:].split(".")[0]
                if layer and target in FORBIDDEN_LAYERS.get(layer, set()):
                    self.add("F8", "high", where, f"{layer}/ imports {target}/: the layers are controllers -> services "
                                                  "-> managers (models from anywhere)")
                continue
            if top[0] in ("features", "modules") and len(top) >= 2:
                if len(top) == 2:   # `from features import registration`: the index of another feature
                    if top[0] == "features" and layer is not None:
                        self.add("F9", "blocker", where, f"`{name}`: import another feature only from its interface")
                    continue
                if top[2] != "interface":
                    self.add("F9", "blocker", where, f"`{name}`: other modules and features only through "
                                                      f"`{'.'.join(top[:2])}.interface` (AGENTS.md call convention 1)")
                if top[0] == "modules" and self.names.get(top[1].replace("_", "-")) and \
                        (FEATURES / self.names[top[1].replace("_", "-")]).is_dir():
                    self.add("F9", "high", where, f"`{name}`: that module is migrated, import "
                                                  f"`features.{self.names[top[1].replace('_', '-')]}.interface`")

    def f10_env(self, path: Path) -> None:
        parts = path.relative_to(self.feature).parts
        if parts[0] == "managers":
            return
        lines = [i for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                 if ENV_READ.search(line) and not line.lstrip().startswith("#")]
        if lines:
            self.add("F10", "low", f"{rel(path)}:{lines[0]}",
                     f"reads the environment ({len(lines)}x): configuration belongs in a manager (`managers/config.py`, "
                     "read at call time, AGENTS.md rule 6) that services call")

    def f11_old_folder(self) -> None:
        if self.module and (MODULES / self.module.replace("-", "_")).is_dir():
            self.add("F11", "high", MODULES / self.module.replace("-", "_"),
                     "the hackathon folder of a migrated module is removed (no second implementation, no adapters)")

    def f12_tests(self) -> None:
        if self.module and not list((ROOT / "tests").glob(f"test_{self.module.replace('-', '_')}_*.py")):
            self.add("F12", "medium", f"tests/test_{self.module.replace('-', '_')}_*.py", "no tests of the feature")

    def f15_readme(self) -> None:
        path = self.feature / "README.md"
        if not path.is_file():
            self.add("F15", "medium", path, "missing: the README names the module it was migrated from "
                                            "and explains what the feature does and how it works")
            return
        text = path.read_text(encoding="utf-8")
        origin = f"modules/{self.module.replace('-', '_')}" if self.module else None
        if origin and origin not in text:
            self.add("F15", "medium", path, f"name the module the feature was migrated from (`{origin}/`)")
        for heading in ("What it does", "How it works"):
            if not re.search(rf"^#+\s+{heading}", text, re.MULTILINE | re.IGNORECASE):
                self.add("F15", "medium", path, f"no section `## {heading}`")

    def f16_models(self) -> None:
        models = self.feature / "models"
        if not (models / "__init__.py").is_file():
            self.add("F16", "medium", models, "missing package: the feature defines its request, step and response "
                                              "models with pydantic in models/ (bases in portal_common.models)")
            return
        uses_pydantic = any(re.search(r"^\s*(from|import)\s+(pydantic|portal_common\.models)\b",
                                      f.read_text(encoding="utf-8"), re.MULTILINE)
                            for f in models.rglob("*.py") if "__pycache__" not in f.parts)
        if not uses_pydantic:
            self.add("F16", "medium", models, "no pydantic model in models/: build the models on pydantic "
                                              "(`portal_common.models.ApiModel`, `RequestBody`, `StepRequest`, `Page`)")

    def f13_header(self, path: Path) -> None:
        head = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:30])
        if "SPDX-License-Identifier" not in head:
            self.add("F13", "medium", path, "no license header (TRG 7.02; copy it from another file of the feature)")
        elif "AI Disclosure" in head and "Assisted-By" not in head:
            self.add("F13", "low", path, "AI disclosure without an `Assisted-By:` line")

    def f14_paths(self, path: Path, tree: ast.Module) -> None:
        if not self.module:
            return
        old = f"/api/{self.module}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and old in node.value \
                    and not path.name == "__init__.py":
                self.add("F14", "medium", f"{rel(path)}:{node.lineno}",
                         f"literal `{old}`: a feature is served under its readable path; use "
                         "`spec.module(MODULE).base_path` or a path relative to it")


def resolve(arg: str, names: dict[str, str]) -> Path:
    candidate = Path(arg)
    if candidate.is_dir():
        return candidate.resolve()
    m = re.search(r"[cC](\d+)[-_][mM](\d+)", arg)
    if m and names.get(f"c{m.group(1)}-m{m.group(2)}"):
        return FEATURES / names[f"c{m.group(1)}-m{m.group(2)}"]
    return FEATURES / arg


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not FEATURES.is_dir():
        print("no features/ in this checkout (feature-first layout, ADR-0003)", file=sys.stderr)
        return 2
    names = spec_names()
    targets = [resolve(a, names) for a in args] or sorted(
        p for p in FEATURES.iterdir() if p.is_dir() and (p / "__init__.py").is_file())
    findings: list[Finding] = []
    for target in targets:
        if not (target / "__init__.py").is_file():
            print(f"not a feature package: {target}", file=sys.stderr)
            return 2
        findings += Checker(target, names).run()
    findings.sort(key=lambda f: (f.feature, SEVERITIES.index(f.severity), f.rule, f.file))
    if as_json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for target in targets:
            mine = [f for f in findings if f.feature == target.name]
            counts = {s: sum(f.severity == s for f in mine) for s in SEVERITIES}
            summary = ", ".join(f"{n} {s}" for s, n in counts.items() if n) or "follows the layout"
            print(f"features/{target.name}: {summary}")
            for f in mine:
                print(f"  [{f.severity}] {f.rule} {f.file}: {f.message}")
    blocking = any(f.severity in ("blocker", "high") for f in findings)
    return 1 if strict and blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

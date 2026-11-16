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
"""The feature-architecture skill (`.claude/skills/feature-architecture`): every feature follows the layout of
ADR-0003, and the checker finds each rule of `features/AGENTS.md` on a feature that breaks it."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude/skills/feature-architecture/scripts/feature-check.py"
HEADER = "# SPDX-License-Identifier: Apache-2.0\n"


def run(*args: str, root: Path | None = None, spec: Path | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("FEATURE_CHECK_ROOT", "SPEC_DIR")}
    if root:
        env["FEATURE_CHECK_ROOT"] = str(root)
    if spec:
        env["SPEC_DIR"] = str(spec)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env, check=False)


def test_every_feature_of_the_repository_follows_the_layout():
    result = run("--strict")
    assert result.returncode == 0, result.stdout + result.stderr


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_the_checker_finds_every_rule_on_a_broken_feature(tmp_path):
    spec = tmp_path / "spec"
    (spec / "C2-M3-TechnicalUser").mkdir(parents=True)
    write(tmp_path, {
        "features/__init__.py": "",
        "features/tech_users/__init__.py": HEADER + 'from features.tech_users.router import router\n'
                                            'NAME = "tech"\nMODULE = "c2-m3"\ndef helper():\n    pass\n',
        "features/tech_users/router.py": HEADER + "from fastapi import APIRouter\nrouter = APIRouter()\n",
        "features/tech_users/interface.py": HEADER,
        "features/tech_users/OPEN-QUESTIONS.md": "",
        "features/tech_users/helpers.py": HEADER,
        "features/tech_users/controllers/__init__.py": "",
        "features/tech_users/controllers/things/controller.py": HEADER,
        "features/tech_users/controllers/items/__init__.py": "",
        "features/tech_users/controllers/items/controller.py": HEADER +
            "from fastapi import APIRouter\nfrom portal_common.routing import Controller\n"
            "from features.tech_users.managers import repo\n"
            'controller = Controller("Items")\n@controller.get("/a/b")\ndef deep():\n    return "/api/c2-m3/items"\n',
        "features/tech_users/services/__init__.py": "",
        "features/tech_users/services/logic.py": HEADER +
            "import os\nfrom fastapi import Request\nfrom features.registration.services import x\n"
            'TOKEN = os.environ.get("TOKEN")\n',
        "features/tech_users/managers/__init__.py": "",
        "features/tech_users/managers/repo.py": "from ..services import logic\n",
        "modules/c2_m3/__init__.py": "",
    })
    (tmp_path / "tests").mkdir()
    result = run("--strict", "--json", root=tmp_path, spec=spec)
    assert result.returncode == 1, result.stderr
    found = json.loads(result.stdout)
    rules = {f["rule"] for f in found}
    expected = {f"F{n}" for n in (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)}
    assert rules >= expected, rules
    messages = " ".join(f["message"] for f in found)
    assert "features/technical_user/" in messages            # F1 names the right folder
    assert "main.py" in " ".join(f["file"] for f in found)   # F2 missing file
    assert "without `__init__.py`" in messages               # F7 blocker: mount() would refuse the tree

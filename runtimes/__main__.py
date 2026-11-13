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
"""`python -m runtimes [name]`: start the runtime `name` (or `RUNTIME`, default `installation`).

The name is a runtime in `runtimes/` (`onboarding`, `installation`) or a feature (`registration`), so one
image serves every pod; only `RUNTIME` differs between the deployments.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys

from runtimes import serve


def factory(name: str) -> str:
    """Import string of the app factory of the runtime or feature `name`."""
    name = name.strip().lower().replace("-", "_")
    for module in (f"runtimes.{name}", f"features.{name}.main"):
        if not name.startswith("_") and importlib.util.find_spec(module.rsplit(".", 1)[0]) \
                and importlib.util.find_spec(module):
            if hasattr(importlib.import_module(module), "create_app"):
                return f"{module}:create_app"
    raise SystemExit(f"unknown runtime {name!r}: neither runtimes/{name}.py nor features/{name}/main.py")


if __name__ == "__main__":
    serve(factory(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RUNTIME", "installation")))

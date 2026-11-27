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
"""Runtime profile of one process (FRAMEWORK 1, ADR-0002, ADR-0003): which features this pod serves.

A runtime in `runtimes/` names its features in code (`create_runtime(registration, company_profile)`);
the generic installation runtime takes them from `ENABLED_FEATURES`, a comma separated list of
readable names or spec ids (`registration,company_profile` or `c1-m2,c3-m1`). None of both means
every module: the modular monolith. Every other module is reached through its address from
`MODULE_URLS` / `<MODULE>_URL` (FRAMEWORK 4.7), so the same image runs as monolith or split.
"""
from __future__ import annotations

import os
from collections.abc import Iterable

from . import spec


def _key(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def resolve(names: Iterable[str]) -> frozenset[str]:
    """Spec ids of features given by readable name or spec id; unknown names fail the start."""
    wanted = {_key(n) for n in names if n.strip()}
    known = spec.modules()
    ids = frozenset(mid for mid, ms in known.items() if _key(mid) in wanted or ms.name in wanted)
    unknown = wanted - {_key(mid) for mid in ids} - {known[mid].name for mid in ids}
    if unknown:
        raise ValueError(f"unknown features: {', '.join(sorted(unknown))}")
    return ids


def enabled_modules(features: Iterable[str] | None = None) -> frozenset[str] | None:
    """The spec ids this process serves: `features` if given, else `ENABLED_FEATURES`, else None (all)."""
    if features is None:
        features = [n for n in os.environ.get("ENABLED_FEATURES", "").split(",") if n.strip()]
    features = list(features)
    return resolve(features) if features else None

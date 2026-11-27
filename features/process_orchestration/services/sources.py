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
"""Sources of a step input and of a lookup (README 6.1, 6.8): field paths, object mappings and `join`."""
from __future__ import annotations

import re


def extract(obj: object, path: str) -> object:
    """Field path (README 6.8): a.b, a[0].b, [0].id, a[TYPE].value (first entry whose `type` is TYPE)."""
    for part in re.findall(r"[^.\[\]]+|\[[^\]]*\]", path):
        if obj is None:
            return None
        if part.startswith("["):
            key = part[1:-1]
            if not isinstance(obj, list):
                return None
            if key.isdigit():
                obj = obj[int(key)] if int(key) < len(obj) else None
            else:
                obj = next((x for x in obj if isinstance(x, dict) and x.get("type") == key), None)
        else:
            obj = obj.get(part) if isinstance(obj, dict) else None
    return obj


def map_fields(raw: object, spec_: object) -> object:
    """README 6.8: a path, an object mapping, or `{join: [paths]}`. Returns None for no value."""
    if isinstance(spec_, str):
        return extract(raw, spec_)
    if isinstance(spec_, dict) and set(spec_) == {"join"}:
        parts = [str(v) for v in (extract(raw, p) for p in spec_["join"]) if v not in (None, "")]
        return " ".join(parts) or None
    if isinstance(spec_, dict):
        out = {k: v for k, v in ((k, map_fields(raw, sub)) for k, sub in spec_.items()) if v is not None}
        return out or None
    return None


def resolve(proc: dict, src: object) -> object:
    """The value of a source: `=constant`, `steps.<key>.<path>`, `lookup.<name>.<field>` or a variable path."""
    if not isinstance(src, str):
        return src
    if src.startswith("="):
        return src[1:]
    if src.startswith("steps."):
        _, key, field = src.split(".", 2)
        sr = next(s for s in proc["steps"] if s["stepKey"] == key)
        return extract(sr["result"] or {}, field)
    if src.startswith("lookup."):
        _, name, field = src.split(".", 2)
        return (proc["lookups"].get(name) or {}).get(field)
    return extract(proc["variables"], src)


def build_input(proc: dict, st: dict, sr: dict) -> dict:
    data = {"processId": proc["id"], "stepRunId": sr["stepRunId"]}
    for field, src in (st.get("input") or {}).items():
        val = resolve(proc, src)
        if val is not None:  # README 6.1: a missing source value is left out
            data[field] = val
    return data


def lookup_result(lk: dict, raw: object) -> dict:
    """The fields of a lookup answer; nothing, an empty list or a 404 is not found (README 6.8)."""
    if not raw:
        return {"found": False}
    res: dict[str, object] = {"found": True}
    for target, fspec in (lk.get("fields") or {}).items():
        val = map_fields(raw, fspec)
        if val is not None:
            res[target] = val
    return res

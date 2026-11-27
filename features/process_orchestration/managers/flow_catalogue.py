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
"""The flow catalogue: `flows.yaml` of the spec, loaded and checked against the spec at start-up (README 6.2).

Steps, lookups and events are named by spec id (`c3-m1.create-company`, `c3-m1.queryCompany`); they are
resolved against the openapi.yaml and README of the module, never against its code, so it does not matter
whether a module is already a feature.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from features.process_orchestration.managers import config
from features.process_orchestration.models.errors import MODULE, FlowError
from portal_common import spec

log = logging.getLogger(MODULE)
OWN_EVENTS = {"ProcessStarted", "ProcessStepFailed", "ProcessCompleted", "ProcessEnded"}


def completion_types(st: dict) -> set[str]:
    """Event names of a step's `completesOn` (a name or an object with `event` and `set`)."""
    return {c["event"] if isinstance(c, dict) else c for c in st.get("completesOn") or []}


def lookup_operation(query: str) -> spec.Operation:
    module, _, op_id = (query or "").partition(".")
    ms = spec.modules().get(module)
    op = next((o for o in (ms.operations if ms else ()) if o.operation_id == op_id), None)
    if op is None or op.method != "GET" or not op.is_query:
        raise FlowError(f"lookup query {query}: no GET operation under /internal with this operationId")
    return op


def known_events() -> set[str]:
    """Event names of the spec: `type` constants of the event schemas in every openapi.yaml
    (FRAMEWORK 6, OP-54; `eventType` in a spec before OP-54), plus the names in the event tables
    (README section 10 of every module, FRAMEWORK section 6)."""
    out = set()
    texts = [(spec.spec_dir() / "FRAMEWORK.md").read_text(encoding="utf-8")]
    texts += [f.read_text(encoding="utf-8") for f in spec.spec_dir().glob("*/README.md")]
    for text in texts:
        m = re.search(r"^## (?:10|6)\. (?:Events|Event catalogue)\n(.*?)(?=^## )", text, re.S | re.M)
        if m:
            out |= set(re.findall(r"^\| `([A-Z][A-Za-z]+)`", m.group(1), re.M))
            out |= {n for row in re.findall(r"^\|[^|]*\| ([^|]+)\|", m.group(1), re.M)
                    for n in re.findall(r"`([A-Z][A-Za-z]+)`", row)}
    for ms in spec.modules().values():
        for name, sch in (ms.document.get("components", {}).get("schemas") or {}).items():
            if name.startswith("Event"):
                props = ms.resolve(sch).get("properties", {})
                for attr in ("type", "eventType"):
                    const = (props.get(attr) or {}).get("const")
                    if isinstance(const, str):
                        out.add(const)
    return out


def check(doc: dict) -> list[str]:
    """README 6.2 against the spec: FlowError for unknown steps, lookups and events, sources that
    are not earlier, and required inputs without a source. Returns the list of warnings (empty
    today); with `FLOWS_CHECK=warn` errors of the last two kinds become warnings."""
    mods = spec.modules()
    lookups = doc.get("lookups") or {}
    for name, lk in lookups.items():
        try:
            lookup_operation(lk.get("query"))
        except FlowError as e:
            raise FlowError(f"lookup {name}: {e}") from None
    events_known = known_events() | OWN_EVENTS
    warnings: list[str] = []
    for fl in doc.get("flows") or []:
        warnings += _check_flow(fl, mods, lookups, events_known)
    return warnings


def _check_flow(fl: dict, mods: dict[str, spec.ModuleSpec], lookups: dict, events_known: set[str]) -> list[str]:
    seen: list[str] = []
    warnings: list[str] = []
    names = {fl["trigger"]["event"], *(fl.get("endOn") or [])}
    for st in fl["steps"]:
        names |= {st["waitFor"]} if st.get("waitFor") else set()
        names |= completion_types(st) | set(st.get("failsOn") or [])
        warnings += _check_step(f"flow {fl['key']}, step {st.get('key')}", st, seen, mods, lookups)
        seen.append(st["key"])
    unknown = sorted(n for n in names if n not in events_known)
    if unknown:
        warnings.append(f"flow {fl['key']}: events {unknown} are not in any event table or schema of the spec")
    return warnings


def _check_step(where: str, st: dict, seen: list[str], mods: dict[str, spec.ModuleSpec], lookups: dict) -> list[str]:
    """FlowError for an unknown step, lookup or source; a warning for a required input without a source."""
    module, _, step = st.get("call", "").partition(".")
    if module not in mods or step not in mods[module].steps():
        raise FlowError(f"{where}: unknown step {st.get('call')}")
    if st.get("lookup") and st["lookup"] not in lookups:
        raise FlowError(f"{where}: unknown lookup {st['lookup']}")
    sources = [s for s in (st.get("input") or {}).values() if isinstance(s, str)] + list(st.get("when") or {})
    for src in sources:
        if src.startswith("steps.") and src.split(".")[1] not in seen:
            raise FlowError(f"{where}: source {src} is not earlier in the flow")
        if src.startswith("lookup.") and src.split(".")[1] not in lookups:
            raise FlowError(f"{where}: unknown lookup in {src}")
    op = mods[module].steps()[step]
    required = set(mods[module].resolve(op.request_schema).get("required", [])) - {"processId", "stepRunId"}
    missing = sorted(required - set(st.get("input") or {}))
    return [f"{where}: required input {missing} of {st['call']} has no source"] if missing else []


def load(flows_file: str | Path | None = None) -> tuple[dict, list[str]]:
    """The flow file (default: `flows.yaml` of the spec) and the warnings of its check; FlowError unless
    `FLOWS_CHECK=warn` when there are warnings."""
    path = Path(flows_file or spec.flows_file())
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    warnings = check(doc)
    if warnings and config.flows_check() != "warn":
        raise FlowError("; ".join(warnings))
    for w in warnings:
        log.warning("flows.yaml: %s", w)
    return doc, warnings

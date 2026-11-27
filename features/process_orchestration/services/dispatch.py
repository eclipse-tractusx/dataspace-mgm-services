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
"""Step dispatch: a step `<module>.<step>` of flows.yaml and a lookup `<module>.<operationId>` go to the module
by its spec id (README 4, 6.8): in-process, over HTTP (`managers.neighbour_client`) or, with an empty
address, to the built-in stand-in (README 11.3)."""
from __future__ import annotations

import copy

from features.process_orchestration.managers import flow_catalogue
from features.process_orchestration.managers import neighbour_client as client
from features.process_orchestration.services import sources
from portal_common import standin


def invoke(proc: dict, st: dict, data: dict, answers: dict, timeout: float) -> dict:
    """Calls the step of `st` with `data`: its answer (`state` DONE or RUNNING) or `{"error": {...}}`."""
    module, _, step = st["call"].partition(".")
    how = client.mode(module)
    if how == client.IN_PROCESS:
        return client.step_in_process(module, step, data)
    if how == client.STANDIN:
        return standin_step(proc, st, data, answers)
    return client.step_over_http(module, step, data, timeout)


def standin_step(proc: dict, st: dict, data: dict, answers: dict) -> dict:
    """README 11.3: DONE at once, no events; `set` of the first completesOn entry applies."""
    result = answers["steps"].get(st["call"])
    if result is None:
        result = standin.standin_result(st["call"], data)
    comp = st.get("completesOn") or []
    if comp and isinstance(comp[0], dict):
        proc["variables"].update(comp[0].get("set") or {})
    return {"stepRunId": data["stepRunId"], "state": "DONE", "result": copy.deepcopy(result)}


def run_lookup(proc: dict, name: str, lk: dict, answers: dict, timeout: float) -> dict:
    """README 6.8: the lookup `name` of the flow file; LookupFailed for an answer other than 200 and 404."""
    op = flow_catalogue.lookup_operation(lk["query"])
    params = {p: sources.resolve(proc, src) for p, src in (lk.get("params") or {}).items()}
    path_params = {p for p in params if "{" + p + "}" in op.path}
    how = client.mode(op.module)
    if how == client.IN_PROCESS:
        raw = client.query_in_process(op, name, {k: v for k, v in params.items()
                                                 if v is not None or k in path_params})
    elif how == client.STANDIN:
        raw = copy.deepcopy(answers["lookups"].get(lk["query"]))
        if isinstance(raw, dict):
            raw.update(params)
    else:
        raw = client.query_over_http(op, name, params, path_params, timeout)
    return sources.lookup_result(lk, raw)

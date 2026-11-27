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
"""Calls of Process Orchestration to the other modules (README 4, 6.8), always addressed by spec id.

The address of a module comes from `portal_common.neighbours` (`<MODULE>_URL`, `MODULE_URLS`):
- `in-process`: the function of the module's interface (`portal_common.layout`, so it does not matter whether
  the module still lives in `modules/<id>/` or is a feature `features/<name>/`), no token;
- an HTTP address: the operation under the module's base path (`spec.module(id).base_path`), with the service
  token of `svc-c12-m1`;
- empty: the built-in stand-in of the engine (`STANDIN`, answered by the services).

A step answers with its result (`state` DONE or RUNNING) or with `{"error": {...}}`; a lookup with the raw
answer (None for 404) or with `LookupFailed`.
"""
from __future__ import annotations

import copy

import httpx

from features.process_orchestration.models.errors import LOOKUP_FAILED, MODULE, FlowError, LookupFailed
from portal_common import http, neighbours, problems, spec, standin, tokens

# the JSON encoding of in-process answers, the same as `neighbours.query` uses (no HTTP involved)
from portal_common.neighbours import jsonable_encoder

IN_PROCESS, STANDIN, HTTP = "in-process", "stand-in", "http"


def mode(module: str) -> str:
    """How `module` is reached: IN_PROCESS, HTTP or STANDIN (empty address, README 11.3)."""
    if neighbours.in_process(module):
        return IN_PROCESS
    return HTTP if neighbours.address(module) else STANDIN


def _auth() -> dict:
    return {"Authorization": "Bearer " + tokens.service_token(MODULE)}


# ---------------------------------------------------------------- steps (README 4, 6.3)
def step_in_process(module: str, step: str, data: dict) -> dict:
    """README 4: `<interface of module>.<step in snake_case>(input)`; a Problem counts like the same
    answer over HTTP (Problem Details with `retryable`)."""
    try:
        fn = standin.interface_function(module, spec.snake_case(step))
        body = jsonable_encoder(fn(copy.deepcopy(data)))
    except Exception as e:  # noqa: BLE001 - every error of a step is an outcome of the step run
        p = problems.to_problem(module, e, True).body()
        return {"error": {"type": p["type"], "status": p["status"], "title": p.get("title"),
                          "detail": p.get("detail"), "retryable": p.get("retryable") is True}}
    if isinstance(body, dict) and body.get("state") in ("DONE", "RUNNING"):
        return body
    return {"error": {"type": "invalid-step-answer", "status": None, "title": f"{module}.{step}: no step result",
                      "retryable": False}}


def step_over_http(module: str, step: str, data: dict, timeout: float) -> dict:
    """`POST <address><base path>/steps/<step>`; timeouts and connection errors are retryable (README 6.3)."""
    base = neighbours.address(module)
    try:
        r = http.request("POST", f"{base}{spec.module(module).base_path}/steps/{step}", json=data,
                         timeout=timeout, headers=_auth())
    except httpx.HTTPError as e:
        return {"error": {"type": "connection", "status": None, "title": type(e).__name__, "retryable": True}}
    try:
        body = r.json()
    except ValueError:
        body = {}
    if r.status_code == 200 and isinstance(body, dict) and body.get("state") in ("DONE", "RUNNING"):
        return body
    body = body if isinstance(body, dict) else {}
    return {"error": {"type": body.get("type", f"http-{r.status_code}"), "status": r.status_code,
                      "title": body.get("title"), "detail": body.get("detail"),
                      "retryable": body.get("retryable") is True}}


# ---------------------------------------------------------------- lookups (README 6.8)
def query_in_process(op: spec.Operation, name: str, params: dict) -> object:
    """`<interface of module>.<operationId in snake_case>(**params)`; a Problem counts like the same answer
    over HTTP: 404 is None (not found), every other error raises LookupFailed."""
    function = op.function_name
    if function is None:    # flow_catalogue.lookup_operation only gives queries with an operationId
        raise FlowError(f"lookup {name}: {op.method} {op.path} is not a query")
    try:
        return jsonable_encoder(standin.interface_function(op.module, function)(**params))
    except Exception as e:  # noqa: BLE001 - every error of a lookup is an error of the step
        p = problems.to_problem(op.module, e, False)
        if p.status == 404:
            return None
        retryable = p.ext["retryable"] if isinstance(p.ext.get("retryable"), bool) else p.status >= 500
        raise LookupFailed({"type": p.body()["type"], "status": p.status,
                            "title": f"lookup {name} answered {p.status}", "retryable": retryable}) from e


def query_over_http(op: spec.Operation, name: str, params: dict, path_params: set[str], timeout: float) -> object:
    """`GET <address><base path><path>` with the path and query parameters; 404 is None (not found)."""
    base = neighbours.address(op.module)
    path = op.path
    for p in path_params:
        path = path.replace("{" + p + "}", str(params[p]))
    try:
        r = http.request("GET", f"{base}{spec.module(op.module).base_path}{path}", timeout=timeout,
                         params={k: v for k, v in params.items() if v is not None and k not in path_params},
                         headers=_auth())
    except httpx.HTTPError as e:
        raise LookupFailed({"type": LOOKUP_FAILED, "status": None, "title": f"lookup {name}: {type(e).__name__}",
                            "retryable": True}) from e
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        try:
            body = r.json() if isinstance(r.json(), dict) else {}
        except ValueError:
            body = {}
        retryable = body["retryable"] if isinstance(body.get("retryable"), bool) else r.status_code >= 500
        raise LookupFailed({"type": body.get("type") or LOOKUP_FAILED, "status": r.status_code,
                            "title": f"lookup {name} answered {r.status_code}", "retryable": retryable})
    return r.json()

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
"""Module registry and installation app: every module and every operation of the spec is mounted."""
from conftest import BASE, bearer, person_token
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portal_common import problems, spec, standin
from scaffold import app as scaffold_app
from scaffold import registry


def test_every_spec_module_has_a_folder_and_a_kind():
    kinds = {e.id: e.kind for e in registry.load()}
    assert set(kinds) == set(spec.modules())
    assert kinds["c12-m1"] == "provided"
    # every other module is a stand-in, the module of a team or a migrated feature (ADR-0003)
    assert {k for k, v in kinds.items() if v not in ("stand-in", "team", "feature")} == {"c12-m1"}
    assert kinds["c1-m2"] == kinds["c3-m1"] == "feature"
    assert [e.id for e in registry.load()][-2:] == ["c11-m1", "c12-m1"]   # subscribers last


def test_every_spec_operation_is_mounted_once():
    app = scaffold_app.create_app()
    paths = TestClient(app, base_url=BASE).get("/openapi.json").json()["paths"]
    for mid, ms in spec.modules().items():
        mounted = {(m.upper(), p) for p, ops in paths.items() for m in ops if p.startswith(ms.base_path + "/")}
        wanted = {(op.method, ms.base_path + op.path) for op in ms.operations}
        assert wanted <= {(m, p) for m, p in mounted}, f"{mid}: {sorted(wanted - mounted)[:3]}"


def test_unimplemented_operation_answers_501_with_permission_check():
    installation = TestClient(scaffold_app.create_app(), base_url=BASE)   # also serves the test IAM
    # the fallback of a module without own routes, independent of whether a team replaced C3-M1
    app = FastAPI()
    problems.install(app)
    app.include_router(standin.fallback_router("c3-m1"))
    c = TestClient(app, base_url=BASE)
    r = c.get("/api/company-profile/osp/change-requests", headers=bearer(person_token("rolf")))
    assert r.status_code == 501 and r.headers["content-type"].startswith("application/problem+json")
    r = c.get("/api/company-profile/osp/change-requests", headers=bearer(person_token("lieschen")))
    assert r.status_code == 403
    assert installation.get("/scaffold/modules").json()[-1] == {"module": "c12-m1", "kind": "provided"}

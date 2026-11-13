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
"""The controllers of a feature mirror the URL they serve (ADR-0003, `portal_common.routing`)."""
from __future__ import annotations

import re
import sys
import textwrap

import pytest

from features.company_profile.router import router as company_profile_router
from features.registration.router import router as registration_router
from portal_common import routing, spec

FEATURE_ROUTERS = {"c1-m2": registration_router, "c3-m1": company_profile_router}


def _routes():
    for module, router in FEATURE_ROUTERS.items():
        for route in router.routes:
            yield module, route


@pytest.mark.parametrize("module", FEATURE_ROUTERS)
def test_every_spec_operation_of_a_migrated_feature_has_a_controller(module):
    served = {(method, route.path) for _, route in _routes() for method in route.methods}
    contract = spec.module(module)
    missing = [f"{op.method} {op.path}" for op in contract.operations
               if (op.method, contract.base_path + op.path) not in served]
    assert not missing


def test_the_folders_of_a_controller_are_the_static_segments_of_its_path():
    for module, route in _routes():
        folders = route.endpoint.__module__.split(".controllers.")[1].split(".")[:-1]
        relative = route.path.removeprefix(spec.module(module).base_path)
        segments = [s for s in relative.split("/") if s and not s.startswith("{")]
        expected = [folder.replace("_", "-") for folder in folders]
        assert segments[:len(expected)] == expected and len(segments) - len(expected) <= 1, route.path


def test_every_operation_checks_the_permission_of_its_spec_operation():
    for _, route in _routes():
        calls = [d.call for d in route.dependant.dependencies]
        assert routing._unmounted not in calls, route.path
        assert any(getattr(call, "__qualname__", "").startswith("require.") for call in calls), route.path


def test_a_controller_rejects_a_path_deeper_than_its_folder():
    controller = routing.Controller("Test")
    for path in ("", "/{applicationId}", "/submit", "/{applicationId}/submit"):
        controller.get(path)(lambda: None)
    with pytest.raises(ValueError, match="sub-folder"):
        controller.get("/{applicationId}/documents/{documentId}")


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """Writes a controller tree as package `tree_<n>` and imports it."""
    monkeypatch.syspath_prepend(str(tmp_path))
    created = []

    def build(files: dict[str, str]):
        name = f"tree_{len(created)}_{id(tmp_path)}"
        created.append(name)
        for relative, source in {"__init__.py": "", **files}.items():
            path = tmp_path / name / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(source))
        return __import__(name)

    yield build
    for name in list(sys.modules):
        if any(name == c or name.startswith(c + ".") for c in created):
            del sys.modules[name]


CONTROLLER = """
    from portal_common.routing import Controller, Permission

    controller = Controller("Test")

    @controller.{method}("{path}")
    def operation(claims: dict = Permission):
        return claims
"""


def test_mount_builds_the_path_from_the_folders_and_the_item_of_the_parent(tree):
    package = tree({
        "applications/__init__.py": 'ITEM = "applicationId"\n',
        "applications/controller.py": CONTROLLER.format(method="post", path="/{applicationId}/submit"),
        "applications/documents/__init__.py": "",
        "applications/documents/controller.py": CONTROLLER.format(method="get", path="/{documentId}"),
    })
    paths = [route.path for route in routing.mount(package, "c1-m2").routes]
    assert paths == ["/api/registration/applications/{applicationId}/submit",
                     "/api/registration/applications/{applicationId}/documents/{documentId}"]


def test_mount_rejects_an_operation_that_is_not_in_the_spec(tree):
    package = tree({"applications/__init__.py": "",
                    "applications/controller.py": CONTROLLER.format(method="delete", path="")})
    with pytest.raises(LookupError, match=re.escape("DELETE /applications")):
        routing.mount(package, "c1-m2")


def test_mount_rejects_an_action_that_is_a_sub_folder(tree):
    package = tree({
        "applications/__init__.py": 'ITEM = "applicationId"\n',
        "applications/controller.py": CONTROLLER.format(method="post", path="/{applicationId}/documents"),
        "applications/documents/__init__.py": "",
    })
    with pytest.raises(ValueError, match="'documents' is a sub-folder"):
        routing.mount(package, "c1-m2")


def test_mount_rejects_a_folder_that_is_not_a_package(tree):
    package = tree({"applications/controller.py": CONTROLLER.format(method="get", path="")})
    with pytest.raises(ValueError, match="no __init__.py"):
        routing.mount(package, "c1-m2")


def test_an_unmounted_permission_fails_loudly():
    with pytest.raises(RuntimeError, match="not mounted"):
        routing._unmounted()

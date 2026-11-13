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
"""Controllers of a feature, organised like the URL they serve (ADR-0003).

The folder `features/<feature>/controllers/` is the base path of the feature (`/api/registration`); every
sub-folder is one path segment (`company_roles/` serves `/company-roles`). A folder's
`controller.py` holds the operations of that path, each with a path relative to its folder:

    ""   "/{applicationId}"   "/submit"   "/{applicationId}/submit"

A sub-folder is a sub-resource of one item of its parent: the parent names that item once in its
`__init__.py` (`ITEM = "applicationId"`), so `applications/documents/` serves
`/applications/{applicationId}/documents`. No controller repeats a path of its folder.

`mount()` turns that tree into the feature's router: it builds every full path, checks that the
operation exists in the module's openapi.yaml, and binds the operation's permission (`x-permission`)
to the parameter declared as `claims: dict = Permission`. A controller checks the token, applies the
scope and calls a service; it holds no business logic.
"""
from __future__ import annotations

import functools
import importlib
import inspect
import pkgutil
import re
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response

from portal_common import problems, spec, standin, tokens

Page = Query(0, ge=0)
Size = Query(20, ge=1, le=100)

company_scope = standin.company_scope   # scope `company` (FRAMEWORK 4.3): another company's object is 404


def _unmounted() -> dict:
    raise RuntimeError("controller is not mounted: build the feature router with portal_common.routing.mount()")


Permission = Depends(_unmounted)
"""Default of the endpoint parameter that receives the token claims; `mount()` replaces it with the
permission check of the operation (`x-permission` in openapi.yaml)."""

# "", "/{item}", "/action" or "/{item}/action": anything deeper is a sub-folder.
_RELATIVE_PATH = re.compile(r"(/\{(?P<item>\w+)\})?(/(?P<action>[a-z0-9]+(-[a-z0-9]+)*))?")


@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    endpoint: Callable
    options: dict


@dataclass
class Controller:
    """The operations of one controller folder, declared like FastAPI routes but relative to the folder."""

    tag: str
    operations: list[Operation] = field(default_factory=list)

    def get(self, path: str = "", **options):
        return self._operation("GET", path, options)

    def post(self, path: str = "", **options):
        return self._operation("POST", path, options)

    def put(self, path: str = "", **options):
        return self._operation("PUT", path, options)

    def patch(self, path: str = "", **options):
        return self._operation("PATCH", path, options)

    def delete(self, path: str = "", **options):
        return self._operation("DELETE", path, options)

    def _operation(self, method: str, path: str, options: dict):
        if not _RELATIVE_PATH.fullmatch(path):
            raise ValueError(f"{method} {path!r} of controller {self.tag!r}: a path is '', '/{{item}}', "
                             "'/action' or '/{item}/action'; deeper paths belong in a sub-folder")

        def register(endpoint: Callable) -> Callable:
            self.operations.append(Operation(method, path, endpoint, options))
            return endpoint
        return register


def mount(controllers: ModuleType, module: str) -> APIRouter:
    """The router of a feature: every operation of the controller tree under the base path of `module`,
    with the module's Problem Details (400 instead of 422, 500 as Problem)."""
    contract = spec.module(module)
    router = APIRouter(route_class=problems.route_class(module))
    for path, controller, sub_folders in _folders(controllers, ""):
        for operation in controller.operations:
            action = _RELATIVE_PATH.fullmatch(operation.path).group("action")
            if action in sub_folders:
                raise ValueError(f"{operation.method} {path}{operation.path}: '{action}' is a sub-folder, "
                                 "declare the operation in its controller.py")
            full = path + operation.path
            if contract.find(operation.method, full) is None:
                raise LookupError(f"{operation.method} {full} of {controllers.__name__} is not in the "
                                  f"openapi.yaml of {module}")
            endpoint = _with_permission(operation.endpoint, tokens.require_spec(module, operation.method, full))
            router.add_api_route(contract.base_path + full, endpoint, methods=[operation.method],
                                 tags=[controller.tag], **operation.options)
    return router


def _folders(package: ModuleType, path: str) -> Iterator[tuple[str, Controller, set[str]]]:
    """Depth first, parents before their sub-folders: (path, controller, path segments of the sub-folders)."""
    children = sorted(info.name for info in pkgutil.iter_modules(package.__path__) if info.ispkg)
    for directory in (d for root in package.__path__ for d in Path(root).iterdir()):
        if directory.is_dir() and directory.name != "__pycache__" and directory.name not in children:
            raise ValueError(f"{directory} has no __init__.py: every folder of the controller tree is a package")
    segments = {name.replace("_", "-") for name in children}
    controller = _controller(package)
    if controller is not None:
        yield path, controller, segments
    item = getattr(package, "ITEM", None)
    for name in children:
        child_path = path + (f"/{{{item}}}" if item else "") + "/" + name.replace("_", "-")
        yield from _folders(importlib.import_module(f"{package.__name__}.{name}"), child_path)


def _controller(package: ModuleType) -> Controller | None:
    if not any(info.name == "controller" for info in pkgutil.iter_modules(package.__path__)):
        return None
    return importlib.import_module(f"{package.__name__}.controller").controller


def _with_permission(endpoint: Callable, check: Callable) -> Callable:
    """The endpoint with `Permission` replaced by the permission check of its operation."""
    signature = inspect.signature(endpoint)
    if not any(p.default is Permission for p in signature.parameters.values()):
        return endpoint
    hints = typing.get_type_hints(endpoint, include_extras=True)   # the wrapper lives in another module
    parameters = [p.replace(annotation=hints.get(p.name, p.annotation),
                            default=Depends(check) if p.default is Permission else p.default)
                  for p in signature.parameters.values()]

    if inspect.iscoroutinefunction(endpoint):
        async def bound(*args, **kwargs):
            return await endpoint(*args, **kwargs)
    else:
        def bound(*args, **kwargs):
            return endpoint(*args, **kwargs)
    functools.update_wrapper(bound, endpoint)
    bound.__signature__ = signature.replace(parameters=parameters,
                                            return_annotation=hints.get("return", signature.return_annotation))
    return bound


def download(info: dict, content: bytes) -> Response:
    """A stored file as attachment (`fileName`, `contentType`), never rendered by the browser."""
    disposition = "attachment; filename*=UTF-8''" + quote(info["fileName"])
    return Response(content, media_type=info["contentType"],
                    headers={"Content-Disposition": disposition, "X-Content-Type-Options": "nosniff"})

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
"""Building blocks of the controllers of a feature (ADR-0003).

A controller is one file in `features/<feature>/controllers/` with its own `router =
controller_router(MODULE, "<Readable tag>")` under the base path of the spec (`/api/c1-m2`), so the
paths, Problem types and permissions stay those of the contract. It checks the token and the
permission of the spec operation (`x-permission`), applies the scope and calls a service; it holds
no business logic. `combined_router()` joins the controllers into the feature's `router.py`.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response

from portal_common import problems, spec, standin, tokens

Page = Query(0, ge=0)
Size = Query(20, ge=1, le=100)

company_scope = standin.company_scope   # scope `company` (FRAMEWORK 4.3): another company's object is 404


def controller_router(module: str, tag: str) -> APIRouter:
    """Router of one controller under the base path of the spec, with the Problem Details of the module
    (400 instead of 422, 500 as Problem)."""
    return APIRouter(prefix=spec.module(module).base_path, route_class=problems.route_class(module), tags=[tag])


def combined_router(*features: APIRouter) -> APIRouter:
    """The controllers of one feature as one router. The routes are copied flat (FastAPI keeps included
    routers lazy, the spec fallback reads `router.routes`); the first controller wins on equal paths."""
    combined = APIRouter()
    for feature in features:
        combined.routes.extend(feature.routes)
    return combined


def permission(module: str, method: str, path: str):
    """Dependency with the permission of the spec operation (`x-permission`); returns the claims."""
    return Depends(tokens.require_spec(module, method, path))


def download(info: dict, content: bytes) -> Response:
    """A stored file as attachment (`fileName`, `contentType`), never rendered by the browser."""
    disposition = "attachment; filename*=UTF-8''" + quote(info["fileName"])
    return Response(content, media_type=info["contentType"],
                    headers={"Content-Disposition": disposition, "X-Content-Type-Options": "nosniff"})

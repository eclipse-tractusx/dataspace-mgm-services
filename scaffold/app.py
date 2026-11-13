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
"""One installation (OSP A or OSP B) as a modular monolith (FRAMEWORK 1).

    SETTINGS_FILE=config/osp-a/installation.json BASE_URL=http://localhost:8000 \
        uv run uvicorn --factory scaffold.app:create_app --port 8000

Start order: settings -> test tools (Portal IAM, EBW-Connector, provider system) -> modules
-> Notifications and Process Orchestration last. All neighbours default to `in-process`.
With `IAM_URL` the Portal IAM is that Keycloak (`iam/`), otherwise the in-memory IAM of the scaffold's
own tests. `TEST_TOOLS=false` leaves all test tools out (then `IAM_URL` and `EBW_CONNECTOR_URL` point
to real systems), and the realm is never reset.
"""
from __future__ import annotations

import contextlib
import json
import os
from collections.abc import Iterable
from typing import Annotated

from fastapi import FastAPI, Query

from controllers.fastapi import include as include_controllers
from portal_common import csp, events, http, problems, runtime, settings, standin, tokens
from tools import iam_backend

from . import registry


def _defaults() -> None:
    base = settings.base_url()
    os.environ.setdefault("MODULE_URLS_DEFAULT", "in-process")
    os.environ.setdefault("EBW_CONNECTOR_URL", base + "/ebw")
    # Configuration variables of the modules for this installation (`moduleConfigFile`, e.g.
    # ATTESTATION_CLIENT_IDS, ISSUER_MODE); the process environment wins. `{BASE_URL}` in a value
    # is the address of the installation.
    file = settings.resolve_path(settings.get("moduleConfigFile"))
    if file and file.exists():
        for k, v in json.loads(file.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                os.environ.setdefault(k, str(v).replace("{BASE_URL}", base))


def reset_all(entries) -> None:
    """Fresh state in every module and test tool (IAM first, C11/C12 last)."""
    from tools import ebw_signer, provider_double, test_iam
    events.RELAY.reset()
    tokens.reset()
    csp.reset()
    test_iam.reset()
    if iam_backend.uses_keycloak() and os.environ.get("TEST_TOOLS", "true") == "true":
        from tools import keycloak_admin
        keycloak_admin.reset_realm()
    provider_double.reset()
    for e in entries:
        if e.module and hasattr(e.module, "reset"):
            e.module.reset()
    _ = ebw_signer  # the signing key stays, so attestations issued before a reset stay valid


def create_app(features: Iterable[str] | None = None) -> FastAPI:
    """The installation app with `features` (readable names or spec ids, `runtimes/`), else the
    features of `ENABLED_FEATURES`, else every module."""
    settings.load()
    _defaults()
    enabled = runtime.enabled_modules(features)
    for mid in enabled or ():   # a split runtime calls its own features in-process, whatever MODULE_URLS says
        os.environ.setdefault(mid.upper().replace("-", "_") + "_URL", "in-process")
    entries = registry.load(enabled)
    events.RELAY.clear_subscribers()

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        events.RELAY.start()
        for e in entries:
            if e.module and hasattr(e.module, "on_startup"):
                e.module.on_startup()
        yield
        events.RELAY.stop()

    app = FastAPI(title=f"Portal installation {settings.get('ospName')}", lifespan=lifespan)
    problems.install(app)
    if os.environ.get("TEST_TOOLS", "true") == "true":
        from tools import ebw_signer, provider_double, test_iam
        for r in (ebw_signer.router, provider_double.router):
            app.include_router(r)
        if not iam_backend.uses_keycloak():
            app.include_router(test_iam.router)
    for e in entries:
        if e.module:
            app.include_router(e.module.router)
        app.include_router(standin.fallback_router(e.id, e.module.router if e.module else None))
        if e.module and hasattr(e.module, "on_event"):
            events.subscribe(e.id, e.module.on_event)
    include_controllers(app)   # APIs of the installation outside the modules, /api/v1/<category>/...
    app.state.entries = entries
    reset_all(entries)

    @app.get("/scaffold/modules", tags=["Scaffold"])
    def modules():
        return [{"module": e.id, "kind": e.kind} for e in entries]

    @app.get("/scaffold/events", tags=["Scaffold"])
    def event_log(type_: Annotated[str | None, Query(alias="type", description="CloudEvents attribute `type`")] = None,
                  eventType: Annotated[str | None, Query(deprecated=True, description="old name of `type`")] = None):
        """Test tool: the CloudEvents published so far (FRAMEWORK 6; no secrets by construction) and
        subscriber failures. `type` filters by the event name; `eventType` is a deprecated alias."""
        want = type_ or eventType
        return {"events": [x for x in events.RELAY.log if not want or x["type"] == want],
                "failures": events.RELAY.failures}

    @app.post("/scaffold/reset", tags=["Scaffold"])
    def reset():
        reset_all(entries)
        return {"reset": True}

    @app.get("/health", tags=["Scaffold"])
    def health():
        return {"status": "UP", "osp": settings.get("ospName")}

    http.register_local(settings.base_url(), app)
    return app



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
"""Runtimes: deployable apps made of features (ADR-0003, Industry Core Hub `runtimes/`).

A runtime imports the features it serves and builds one app from them; every other module is a
neighbour, reached in-process when it runs in the same pod, otherwise over HTTP (`MODULE_URLS`,
FRAMEWORK 4.7). The same image runs every runtime:

    runtimes/installation.py         every module, the modular monolith (default; `ENABLED_FEATURES` narrows it)
    runtimes/onboarding.py           hybrid: registration + company profile in one pod
    features/<feature>/main.py       one feature alone

    RUNTIME=onboarding python -m runtimes          # what the container runs (Dockerfile CMD)
    uv run uvicorn --factory runtimes.onboarding:create_app --port 8000
"""
from __future__ import annotations

import os
from collections.abc import Callable
from types import ModuleType

from fastapi import FastAPI


def create_runtime(*features: ModuleType | str) -> FastAPI:
    """App serving `features`: feature packages (`from features import registration`) or the readable
    names / spec ids of modules that are not migrated yet (`"process_orchestration"`, `"c12-m1"`)."""
    from scaffold import app

    return app.create_app([f.NAME if isinstance(f, ModuleType) else f for f in features])


def serve(create_app: Callable[[], FastAPI] | str) -> None:
    """Run an app factory with uvicorn on `HOST`:`PORT` (default 0.0.0.0:8000)."""
    import uvicorn

    uvicorn.run(create_app, factory=True, host=os.environ.get("HOST", "0.0.0.0"),   # noqa: S104 (container)
                port=int(os.environ.get("PORT", "8000")))

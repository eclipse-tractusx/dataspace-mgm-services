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
#  Assisted-By: GitHub Copilot
#################################################################################
"""App Access as its own runtime (one pod; every other module is a neighbour, ADR-0002, FRAMEWORK 4.7):

    SETTINGS_FILE=config/osp-a/installation.json BASE_URL=http://localhost:8202 \
    C2_M2_DATABASE_URL=postgresql://... IAM_URL=http://localhost:8080/auth IAM_REALM=CX-Central \
        uv run uvicorn --factory features.app_access.main:create_app --port 8202
    RUNTIME=app_access python -m runtimes

Serves the API of the spec under /api/app-access, plus /health and Swagger at /docs. Neighbours (C3-M1,
Subscriptions) are reached through `C3_M1_URL`, `C10_M1_URL` or `MODULE_URLS`; without an address App Access uses
its built-in stand-ins (README 11.2). Without `IAM_URL` and with `TEST_TOOLS` not `false`, the in-memory test IAM
is mounted at /auth, as in the installation.
"""
from __future__ import annotations

from fastapi import FastAPI

from features import app_access
from runtimes import create_runtime, serve


def create_app() -> FastAPI:
    return create_runtime(app_access)


if __name__ == "__main__":
    serve(create_app)

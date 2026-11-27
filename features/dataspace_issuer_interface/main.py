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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""Standalone application for the Dataspace Issuer Interface caller."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions.interface_api_error import InterfaceApiError
from .exceptions.issuer_caller_error import IssuerCallerError
from .router import router


def create_app() -> FastAPI:
    """Build the standalone issuer-caller application."""
    app = FastAPI(title="Dataspace Issuer Interface")

    @app.exception_handler(InterfaceApiError)
    async def handle_interface_api_error(_: Request, error: InterfaceApiError) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

    @app.exception_handler(IssuerCallerError)
    async def handle_issuer_caller_error(_: Request, error: IssuerCallerError) -> JSONResponse:
        status_code = 502 if error.retryable else 409
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    app.include_router(router)
    return app

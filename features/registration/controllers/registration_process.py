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
"""Registration: steps of Process Orchestration (README 8) and internal queries (README 9).
"""
from __future__ import annotations

from typing import Literal

from fastapi import Body, Query

from features.registration.services import application_process_service
from features.registration.services.shared import MODULE
from portal_common.routing import controller_router, permission

router = controller_router(MODULE, "Registration: Process Steps and Queries")


# ------------------------------------------------------------------------- steps and queries (8, 9)
@router.post("/steps/complete-application")
def step_complete_application(body: dict = Body(...),
                              _: dict = permission(MODULE, "POST", "/steps/complete-application")):
    return application_process_service.complete_application(body)


@router.post("/steps/close-application")
def step_close_application(body: dict = Body(...), _: dict = permission(MODULE, "POST", "/steps/close-application")):
    return application_process_service.close_application(body)


@router.get("/internal/applications/{applicationId}")
def get_application_internal(applicationId: str,
                             _: dict = permission(MODULE, "GET", "/internal/applications/{applicationId}")):
    return application_process_service.get_application_internal(applicationId=applicationId)


@router.get("/internal/applications")
def list_applications_internal(applicationId: list[str] = Query(..., max_length=100),
                               _: dict = permission(MODULE, "GET", "/internal/applications")):
    return application_process_service.list_applications_internal(applicationId=applicationId)


@router.get("/internal/agreements")
def list_agreements_internal(status: Literal["ACTIVE", "INACTIVE"] | None = None,
                             _: dict = permission(MODULE, "GET", "/internal/agreements")):
    return application_process_service.list_agreements_internal(status=status)

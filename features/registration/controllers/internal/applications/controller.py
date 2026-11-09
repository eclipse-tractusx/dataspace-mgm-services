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
"""Applications for other modules (README 9.1, 9.2)."""
from __future__ import annotations

from fastapi import Query

from features.registration.services import application_process_service
from portal_common.routing import Controller, Permission

controller = Controller("Registration: Process Steps and Queries")


@controller.get("/{applicationId}")
def get_application_internal(applicationId: str, _: dict = Permission):
    return application_process_service.get_application_internal(applicationId=applicationId)


@controller.get("")
def list_applications_internal(applicationId: list[str] = Query(..., max_length=100), _: dict = Permission):
    return application_process_service.list_applications_internal(applicationId=applicationId)

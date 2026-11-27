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
"""README 7.8: the applicant follows the processes of their own application; another person's
application gives an empty stream, never a 404."""
from __future__ import annotations

from fastapi import Header, Request
from fastapi.responses import StreamingResponse

from features.process_orchestration import interface
from portal_common import sse
from portal_common.routing import Controller, Permission

controller = Controller("Process Orchestration: Live State")


@controller.get("", summary="Live changes of the processes of the own application")
def stream_application_process_events(applicationId: str, request: Request, claims: dict = Permission,
                                      last_event_id: str | None = Header(None, alias="Last-Event-ID"),
                                      ) -> StreamingResponse:
    stream = interface.application_stream(applicationId, claims["sub"])   # 400 for an id that is no UUID
    return sse.response(stream.broker, request, claims, last_event_id, visible=stream.visible, initial=stream.initial)

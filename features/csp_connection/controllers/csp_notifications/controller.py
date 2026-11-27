#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
"""Notifications of the CSP (README 7.2), called by the CSP's service account."""
from __future__ import annotations

from features.csp_connection import interface
from features.csp_connection.models.schemas import CspNotification
from portal_common.routing import Controller, Permission

controller = Controller("CSP Connection: CSP")


@controller.post("", operation_id="receiveCspNotification", summary="Notification from the CSP")
def receive_csp_notification(body: CspNotification, _: dict = Permission) -> dict[str, str | bool]:
    """README 7.2, called by the CSP's service account (`report_csp_notification`).
    A known `notificationId` answers 200 and is not processed again."""
    return interface.receive_csp_notification(body.to_json())

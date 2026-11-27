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
"""C3-M2 services: `steps` for Process Orchestration, `queries` for other modules and OSP staff, `notifications`
for the callbacks of the CSP; `registration_state` holds the status changes they share."""
from __future__ import annotations

from features.csp_connection.managers import csp_client, store
from features.csp_connection.services.common import StepReply
from features.csp_connection.services.notifications import receive_csp_notification
from features.csp_connection.services.queries import find_companies, get_csp_registration, registration_view
from features.csp_connection.services.steps import (
    deregister_connector,
    deregister_membership,
    register_company,
    register_connector,
    register_did,
    register_membership,
    transfer_company,
    update_company,
)

__all__ = [
    "StepReply", "deregister_connector", "deregister_membership", "find_companies", "get_csp_registration",
    "receive_csp_notification", "register_company", "register_connector", "register_did", "register_membership",
    "registration_view", "reset", "start", "transfer_company", "update_company",
]


def start() -> None:
    """Start of a runtime: the tables exist and hold the seed data of README 4."""
    store.create_tables()
    store.seed()


def reset() -> None:
    """Fresh state: own tables empty, then the seed data of README 4; new built-in CSP stand-in."""
    csp_client.reset()
    store.reset()

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
"""Public interface of C3-M2 CSP Connection (call convention of AGENTS.md).

Steps for Process Orchestration (README 8), the query `find-companies` (README 9), the callback
of the CSP (README 7.2) and the status of a company at the CSP (README 7.1). No token checks
here: the controllers check token and permission, a caller in the same process has none.

Steps take the JSON body as a plain dict (`StepInputJson`) and answer a `StepReply`
(FRAMEWORK 4.4). The HTTP contract of the same operations is in `models/schemas.py`. Other modules
and Process Orchestration import only from here; the logic lives in `services/`.
"""
from __future__ import annotations

from features.csp_connection.models.errors import MODULE
from features.csp_connection.services import (
    StepReply,
    deregister_connector,
    deregister_membership,
    find_companies,
    get_csp_registration,
    receive_csp_notification,
    register_company,
    register_connector,
    register_did,
    register_membership,
    registration_view,
    reset,
    transfer_company,
    update_company,
)

__all__ = [
    "MODULE",
    "StepReply",
    "deregister_connector",
    "deregister_membership",
    "find_companies",
    "get_csp_registration",
    "receive_csp_notification",
    "register_company",
    "register_connector",
    "register_did",
    "register_membership",
    "registration_view",
    "reset",
    "transfer_company",
    "update_company",
]

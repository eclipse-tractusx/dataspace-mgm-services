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
"""Status of a company at the CSP, for OSP staff (README 7.1)."""
from __future__ import annotations

from uuid import UUID

from features.csp_connection import interface
from features.csp_connection.models.schemas import CspRegistration
from portal_common.routing import Controller, Permission

controller = Controller("CSP Connection: OSP")


@controller.get("/{companyId}", operation_id="getCspRegistration", summary="Status of a company at the CSP",
                response_model=CspRegistration, response_model_exclude_none=True)
def get_csp_registration(companyId: UUID,  # openapi name (format uuid: a malformed id is 400 validation)
                         _: dict = Permission) -> dict[str, str]:
    """README 7.1, for OSP staff (`view_csp_registration`). 404 without a registration."""
    return interface.get_csp_registration(companyId=str(companyId))

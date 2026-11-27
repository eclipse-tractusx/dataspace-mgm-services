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
"""The credentials of the own company (README 7.1), scope `company`."""
from __future__ import annotations

from features.credentials import interface
from features.credentials.models.credentials import CredentialStatusView
from features.credentials.models.errors import MODULE
from portal_common.routing import Controller, Permission, company_scope

controller = Controller("Credentials: Company Credentials")


@controller.get("", response_model=list[CredentialStatusView], summary="Credentials of the own company")
def own_credentials(companyId: str, claims: dict = Permission) -> list[CredentialStatusView]:
    """README 7.1; order of checks per 6.5: token, permission, then `company_id` of the token = `companyId`."""
    company_scope(MODULE, claims, companyId)
    return interface.own_credentials(companyId)

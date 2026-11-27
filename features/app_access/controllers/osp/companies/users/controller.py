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
"""One person of any company for the OSP staff (README 7.14), scope `osp`."""
from __future__ import annotations

from features.app_access.interface import osp_actor, services
from features.app_access.models.exception_translator import translated
from portal_common.routing import Controller, Permission

controller = Controller("App Access: OSP Users")


@controller.delete("/{userId}", status_code=204, response_model=None, operation_id="removeUserAsOsp",
                   summary="Remove a person from any company")
@translated
def remove_user_as_osp(companyId: str, userId: str, claims: dict = Permission) -> None:
    services().users.remove_company_user(companyId, userId, osp_actor(claims), as_osp=True)

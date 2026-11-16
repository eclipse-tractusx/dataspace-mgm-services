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
#  Assisted-By: GitHub Copilot
#################################################################################
"""The OSP staff (README 7.15), scope `osp`."""
from __future__ import annotations

from features.app_access.models import Page as Paged, StaffMember
from features.app_access.models.exception_translator import translated
from features.app_access.interface import services
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("App Access: OSP Staff")


@controller.get("", operation_id="listStaff", response_model=Paged[StaffMember], summary="List the OSP staff")
@translated
def list_staff(page: int = Page, size: int = Size,
               claims: dict = Permission) -> Paged[StaffMember]:
    return services().users.list_staff(page, size)

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
"""Can an account be used for a connector? (README 9.1)"""
from __future__ import annotations

from features.technical_user import interface
from features.technical_user.models.responses import WIRE, TechnicalUserCheck
from portal_common.routing import Controller, Permission

controller = Controller("Technical User: Process Steps and Queries")


@controller.get("/{id}", summary="Can the account be used for a connector?", response_model=TechnicalUserCheck,
                **WIRE)
def check_technical_user(id: str, companyId: str, offerSubscriptionId: str | None = None, _: dict = Permission) -> dict:
    return interface.check_technical_user(id=id, companyId=companyId, offerSubscriptionId=offerSubscriptionId)

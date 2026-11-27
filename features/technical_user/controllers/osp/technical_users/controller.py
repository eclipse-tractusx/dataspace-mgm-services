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
"""The technical users of all companies, for the OSP (README 7.7, 7.8)."""
from __future__ import annotations

from fastapi import Query

from features.technical_user import interface
from features.technical_user.models import Origin, Status, WalletAccess
from features.technical_user.models.responses import WIRE, TechnicalUser, TechnicalUserSummary
from portal_common import models
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("Technical User: OSP Overview")


@controller.get("", summary="List the technical users of all companies",
                response_model=models.Page[TechnicalUserSummary], **WIRE)
def list_all_technical_users(page: int = Page, size: int = Size, companyId: str | None = None,
                             status: list[Status] | None = Query(None), origin: Origin | None = None,
                             walletAccess: WalletAccess | None = None, disabled: bool | None = None,
                             _: dict = Permission) -> dict:
    return interface.list_all_technical_users(page=page, size=size, company_id=companyId, status=status,
                                              origin=origin, wallet_access=walletAccess, disabled=disabled)


@controller.get("/{id}", summary="Details of any technical user", response_model=TechnicalUser, **WIRE)
def get_any_technical_user(id: str, _: dict = Permission) -> dict:
    return interface.get_any_technical_user(id=id)

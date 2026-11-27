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
"""The technical users of the own company (README 7.1 to 7.6), scope `company`."""
from __future__ import annotations

from fastapi import Body, Query
from fastapi.responses import JSONResponse, Response

from features.technical_user import interface
from features.technical_user.models import Origin, Status, WalletAccess
from features.technical_user.models.errors import MODULE
from features.technical_user.models.responses import (
    WIRE,
    AssignableRole,
    TechnicalUser,
    TechnicalUserSummary,
    TechnicalUserWithCredentials,
)
from portal_common import models
from portal_common.routing import Controller, Page, Permission, Size, company_scope

controller = Controller("Technical User: Technical Users")
LANG = Query("de", pattern="^[a-z]{2}$")


@controller.get("", summary="List the technical users visible to the company",
                response_model=models.Page[TechnicalUserSummary], **WIRE)
def list_technical_users(companyId: str, page: int = Page, size: int = Size,
                         status: list[Status] | None = Query(None), origin: Origin | None = None,
                         walletAccess: WalletAccess | None = None, claims: dict = Permission) -> dict:
    company_scope(MODULE, claims, companyId)
    return interface.list_technical_users(company_id=companyId, page=page, size=size, status=status,
                                          origin=origin, wallet_access=walletAccess)


@controller.post("", status_code=201, summary="Create a technical user",
                 response_model=TechnicalUserWithCredentials, **WIRE)
def create_technical_user(companyId: str, body: dict = Body(...), claims: dict = Permission) -> dict:
    company_scope(MODULE, claims, companyId)
    return interface.create_technical_user(company_id=companyId, body=body, actor_sub=claims["sub"])


@controller.get("/assignable-roles", summary="Roles that the company can assign",
                response_model=list[AssignableRole], **WIRE)
def list_assignable_roles(companyId: str, lang: str = LANG, claims: dict = Permission) -> list[dict]:
    company_scope(MODULE, claims, companyId)
    return interface.list_assignable_roles(company_id=companyId, lang=lang)


@controller.get("/{id}", summary="Details of a technical user", response_model=TechnicalUser, **WIRE)
def get_technical_user(companyId: str, id: str, claims: dict = Permission) -> dict:
    company_scope(MODULE, claims, companyId)
    return interface.get_technical_user(id=id, company_id=companyId)


@controller.patch("/{id}", summary="Change name, description or roles", response_model=TechnicalUser, **WIRE)
def update_technical_user(companyId: str, id: str, body: dict = Body(...), claims: dict = Permission) -> dict:
    company_scope(MODULE, claims, companyId)
    return interface.update_technical_user(id=id, company_id=companyId, body=body, actor_sub=claims["sub"])


@controller.delete("/{id}", status_code=204, summary="Delete a technical user")
def delete_technical_user(companyId: str, id: str, claims: dict = Permission) -> Response:
    company_scope(MODULE, claims, companyId)
    status_code, account = interface.delete_technical_user(id=id, company_id=companyId, actor_sub=claims["sub"])
    if status_code == 202:
        return JSONResponse(account, status_code=202)
    return Response(status_code=204)

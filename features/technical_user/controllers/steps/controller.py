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
"""The steps of the technical users in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from fastapi import Body

from features.technical_user import interface
from features.technical_user.models.responses import (
    WIRE,
    CompanyTechnicalUsers,
    SubscriptionAccounts,
    SubscriptionTechnicalUsers,
    WalletResult,
)
from portal_common.models import StepResult
from portal_common.routing import Controller, Permission

controller = Controller("Technical User: Process Steps and Queries")


@controller.post("/create-for-subscription", summary="Step: create-for-subscription",
                 response_model=StepResult[SubscriptionAccounts], **WIRE)
def step_create_for_subscription(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.create_for_subscription(body)


@controller.post("/apply-wallet-access", summary="Step: apply-wallet-access",
                 response_model=StepResult[WalletResult], **WIRE)
def step_apply_wallet_access(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.apply_wallet_access(body)


@controller.post("/delete", summary="Step: delete",
                 response_model=StepResult[WalletResult], **WIRE)
def step_delete(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.delete(body)


@controller.post("/disable-company-technical-users", summary="Step: disable-company-technical-users",
                 response_model=StepResult[CompanyTechnicalUsers], **WIRE)
def step_disable_company_technical_users(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.disable_company_technical_users(body)


@controller.post("/enable-company-technical-users", summary="Step: enable-company-technical-users",
                 response_model=StepResult[CompanyTechnicalUsers], **WIRE)
def step_enable_company_technical_users(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.enable_company_technical_users(body)


@controller.post("/disable-subscription-technical-users", summary="Step: disable-subscription-technical-users",
                 response_model=StepResult[SubscriptionTechnicalUsers], **WIRE)
def step_disable_subscription_technical_users(body: dict = Body(...), _: dict = Permission) -> dict:
    return interface.disable_subscription_technical_users(body)

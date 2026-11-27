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
"""The steps of the dataspace wallets in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from features.dataspace_wallet_interface import interface
from features.dataspace_wallet_interface.models.api import (
    CreateWalletInput,
    WalletAccountInput,
    WalletAccountStepReply,
    WalletStepReply,
)
from portal_common.routing import Controller, Permission

controller = Controller("Dataspace Wallet Interface: Steps")
# A step result leaves out the optional fields that are empty, as the services build it.
WALLET = {"response_model": WalletStepReply, "response_model_exclude_unset": True}
ACCOUNT = {"response_model": WalletAccountStepReply, "response_model_exclude_unset": True}


def _input(body: CreateWalletInput | WalletAccountInput) -> dict:
    """The step input as the in-process contract takes it: the JSON fields the caller sent."""
    return body.model_dump(by_alias=True, exclude_unset=True)


@controller.post("/create-wallet", summary="Step: create-wallet", **WALLET)
def step_create_wallet(body: CreateWalletInput, _: dict = Permission) -> dict:
    return interface.create_wallet(_input(body))


@controller.post("/create-wallet-account", summary="Step: create-wallet-account", **ACCOUNT)
def step_create_wallet_account(body: WalletAccountInput, _: dict = Permission) -> dict:
    return interface.create_wallet_account(_input(body))


@controller.post("/delete-wallet-account", summary="Step: delete-wallet-account", **ACCOUNT)
def step_delete_wallet_account(body: WalletAccountInput, _: dict = Permission) -> dict:
    return interface.delete_wallet_account(_input(body))

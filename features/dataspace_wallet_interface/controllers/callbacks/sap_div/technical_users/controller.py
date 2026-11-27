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
"""SAP DIV reports a created or deleted wallet account (README 7.6)."""
from __future__ import annotations

from fastapi import Body, Response

from features.dataspace_wallet_interface import interface
from portal_common.routing import Controller, Permission

controller = Controller("Dataspace Wallet Interface: Provider")


@controller.post("/{externalId}", summary="Callback: SAP DIV created the wallet account")
def sap_div_wallet_account_created(externalId: str, body: dict = Body(...), claims: dict = Permission) -> Response:
    interface.sap_div_wallet_account_created(externalId, body, claims)
    return Response(status_code=204)


@controller.post("/{externalId}/delete", summary="Callback: SAP DIV deleted the wallet account")
def sap_div_wallet_account_deleted(externalId: str, claims: dict = Permission) -> Response:
    interface.sap_div_wallet_account_deleted(externalId, claims)
    return Response(status_code=204)

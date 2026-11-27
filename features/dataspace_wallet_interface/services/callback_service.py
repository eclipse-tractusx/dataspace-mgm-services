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
#  Assisted-By: Claude Code (claude-sonnet-5-5)
#################################################################################
"""The SAP DIV callbacks (README 7.6): the middleware reports wallets and wallet accounts.

Checks in this order: token (401) and permission `submit_wallet_callback` (403) in the controller
`callbacks/sap_div/`, then here the calling client `azp` equals `SAP_DIV_CALLBACK_CLIENT_ID` (403, nothing is
audited), then the logic of the core (`wallet_service`) or of the wallet accounts (`account_service`), which
writes the audit entry itself.
"""
from __future__ import annotations

from ..managers import config
from ..models import errors
from . import account_service, wallet_service


def _authorize(claims: dict) -> None:
    if claims.get("azp") != config.sap_div_callback_client_id():
        raise errors.problem(403, "forbidden", "the calling client is not the callback client of SAP DIV")


def wallet_created(bpn: str, body: dict, claims: dict) -> None:
    """`POST /callbacks/sap-div/wallets/{bpn}`."""
    _authorize(claims)
    wallet_service.accept_wallet_callback(bpn, body, claims)


def account_created(external_id: str, body: dict, claims: dict) -> None:
    """`POST /callbacks/sap-div/technical-users/{externalId}`."""
    _authorize(claims)
    account_service.accept_account_created(external_id, body, claims)


def account_deleted(external_id: str, claims: dict) -> None:
    """`POST /callbacks/sap-div/technical-users/{externalId}/delete`."""
    _authorize(claims)
    account_service.accept_account_deleted(external_id, claims)

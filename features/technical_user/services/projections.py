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
#  Assisted-By: GitHub Copilot (Claude Sonnet 5.5)
#################################################################################
"""API shapes of a technical user (`TechnicalUserSummary`, `TechnicalUser`, `Credentials`)."""
from __future__ import annotations

from portal_common import tokens

from ..managers import config
from ..models import TechnicalUserRecord, Viewer, WalletAccess
from ..models.responses import Credentials, TechnicalUser, TechnicalUserSummary, TechnicalUserWithCredentials
from ..models.schemas import role_refs
from . import iam_access


def summary(row: TechnicalUserRecord, viewer: Viewer) -> TechnicalUserSummary:
    return TechnicalUserSummary.model_validate(_fields(row) | {"viewer_role": viewer})


def details(row: TechnicalUserRecord, viewer: Viewer, roles: list[str] | None = None) -> TechnicalUser:
    """7.3: the roles come from the Portal IAM (or are given by the caller, who has just set them); with wallet
    access the wallet role is listed too, and the wallet account only while it is active."""
    if roles is None:
        roles = iam_access.call(iam_access.iam().roles_for, row["iam_client_id"]) if row["iam_client_uuid"] else []
    if row["wallet_access"] != WalletAccess.NONE:
        roles = sorted(set(roles) | config.wallet_roles())
    extra = {"wallet_account_ref": row["wallet_account_ref"]} if row["wallet_access"] == WalletAccess.ACTIVE else {}
    return TechnicalUser.model_validate(_fields(row) | extra | {
        "viewer_role": viewer, "auth_method": "SECRET", "roles": role_refs(roles)})


def with_credentials(user: TechnicalUser, row: TechnicalUserRecord, secret: str) -> TechnicalUserWithCredentials:
    return TechnicalUserWithCredentials.model_validate(
        user.model_dump(exclude_unset=True) | {"credentials": credentials(row, secret)})


def credentials(row: TechnicalUserRecord, secret: str) -> Credentials:
    return Credentials(iam_client_id=row["iam_client_id"], secret=secret, token_url=tokens.token_endpoint())


def _fields(row: TechnicalUserRecord) -> dict:
    """The fields of the row that the summary shows (the row holds more, e.g. the IAM IDs)."""
    return {name: value for name, value in row.items() if name in TechnicalUserSummary.model_fields}

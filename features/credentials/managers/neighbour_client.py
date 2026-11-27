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
"""Neighbours of the credentials (README 11.1, 11.2): C3-M1 Company Profile and C4-M2 Dataspace Wallet Interface.

Every call goes through `portal_common.neighbours`, in process or over HTTP (`COMPANY_URL`, `WALLET_URL`).
"""
from __future__ import annotations

from features.credentials.models.errors import MODULE
from portal_common import neighbours


def company(company_id: str) -> dict | None:
    """C3-M1 `query_company`: status and BPN of the company."""
    return neighbours.query(MODULE, "c3-m1", "query_company", companyId=company_id)


def wallet(company_id: str) -> dict | None:
    """C4-M2 `get_wallet_info`: status, DID, provider and issuance mode of the dataspace wallet."""
    return neighbours.query(MODULE, "c4-m2", "get_wallet_info", companyId=company_id)


def holder_access(company_id: str) -> dict | None:
    """C4-M2 `get_holder_access`: access to the holder's wallet, given only to this module."""
    return neighbours.query(MODULE, "c4-m2", "get_holder_access", companyId=company_id)

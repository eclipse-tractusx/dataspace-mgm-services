#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
"""Duplicate check at the CSP for C1-M3 (README 9)."""
from __future__ import annotations

from typing import Any

from fastapi import Query

from features.csp_connection import interface
from features.csp_connection.models.schemas import CspCompanyMatch
from portal_common.routing import Controller, Permission

controller = Controller("CSP Connection: Queries")


@controller.get("", operation_id="findCompanies", summary="Duplicate check at the CSP",
                response_model=list[CspCompanyMatch], response_model_exclude_none=True)
def find_companies(_: dict = Permission,
                   ebwoid: str | None = None, euid: str | None = None,
                   identifier: list[str] = Query(default=[], description="<type>:<value>, repeatable"),
                   legalName: str | None = None,  # openapi name
                   country: str | None = Query(default=None, pattern=r"^[A-Z]{2}$")) -> list[dict[str, Any]]:
    """README 9, duplicate check for C1-M3. At least `ebwoid`, `euid`, `identifier`, or
    `legalName` with `country`. An empty list means no match."""
    return interface.find_companies(ebwoid=ebwoid, euid=euid, identifier=identifier, legalName=legalName,
                                    country=country)

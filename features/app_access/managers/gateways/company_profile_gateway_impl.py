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
#  Assisted-By: GitHub Copilot (claude-opus-5-5)
#################################################################################
from __future__ import annotations

from features.app_access.managers.ports import CompanyProfileGateway
from features.app_access.models.exception import UpstreamErrorException

from .neighbour_gateway import NeighbourGateway


class CompanyProfileGatewayImpl(NeighbourGateway, CompanyProfileGateway):
    """C3-M1 Company Profile: a company without a row in the table `company` (6.6)."""

    TARGET = "c3-m1"
    STUB_FILE = "stub-companies.json"

    def company(self, company_id: str) -> dict | None:
        if self.is_standin():
            return next((c for c in self.stub_items() if c["id"] == company_id), None)
        found = self.query("query_company", companyId=company_id)
        if isinstance(found, list):
            raise UpstreamErrorException(f"{self.TARGET} query_company gave a list, not a company", retryable=True)
        return found

    def active_companies_with(self, identifier: str) -> list[str]:
        if self.is_standin():
            return [c["id"] for c in self.stub_items()
                    if c["status"] == "ACTIVE" and identifier in (c.get("ebwoid"), c.get("euid"))]
        found = self.query("find_identifier_matches", statuses=["ACTIVE"],
                           identifiers=[{"type": kind, "value": identifier} for kind in ("EBWOID", "EUID")])
        if not isinstance(found, dict):
            raise UpstreamErrorException(f"{self.TARGET} find_identifier_matches gave no result", retryable=True)
        return [match["companyId"] for match in found.get("matches") or []]

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
"""Response models of change requests (README 7.4 to 7.6, 7.14 to 7.18).

The company sees its own requests without `companyName` and `decidedBy` (`ChangeRequest`); OSP staff see
both (`ReviewedChangeRequest`) and, for one request, the current state of the company (`ChangeRequestDetail`).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from features.company_profile.models.company import Address, Identifier
from features.company_profile.models.value_sets import ChangeRequestStatus, CompanyStatus, CoreDataSource
from portal_common.models import ApiModel


class DocumentInfo(ApiModel):
    id: str
    file_name: str
    media_type: str
    size_bytes: int


class ChangeRequest(ApiModel):
    id: str
    company_id: str
    status: ChangeRequestStatus
    changes: dict[str, Any]
    comment: str | None = None
    documents: list[DocumentInfo]
    requested_by: str | None = None
    created_at: str
    closed_at: str | None = None
    decision_reason: str | None = None


class ReviewedChangeRequest(ChangeRequest):
    company_name: str | None = None
    decided_by: str | None = None


class ChangeRequestCompany(ApiModel):
    """The company as it is now, next to the requested changes (7.15)."""

    id: str | None = None
    name: str | None = None
    address: Address
    identifiers: list[Identifier]
    core_data_source: CoreDataSource | None = None
    status: CompanyStatus | None = None


class ChangeRequestDetail(ReviewedChangeRequest):
    company: ChangeRequestCompany


class DocumentContent(BaseModel):
    """A stored document for the download of 7.16: bytes, media type and file name (no JSON)."""

    content: bytes
    media_type: str
    file_name: str

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
"""The API contract of C3-M2 as pydantic models: one class per schema in `components.schemas` of
`spec/C3-M2-CSPConnection/openapi.yaml`, with the same names. Attributes are snake_case in Python, the
JSON fields camelCase as on the wire (`portal_common.models.ApiModel`).

The controllers use them so that FastAPI validates every HTTP request (400 `validation` as Problem
Details, never 422) and Swagger UI at `/docs` shows the real fields; a controller passes the body on
with `to_json()`. `interface.py` keeps plain dicts: Process Orchestration calls the interface functions
in-process with dicts (call convention of AGENTS.md), and the interface checks its input itself.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationError

from portal_common import models
from portal_common.models import ApiModel, CountryCode, StepRequest, Uuid

RegistrationStatus = Literal["PENDING", "REGISTERED", "FAILED", "TRANSFERRED_AWAY"]   # README 6.1
Membership = Literal["NONE", "REGISTERED", "DEREGISTERED"]
NotificationType = Literal["OperationCompleted", "CompanyTransferredAway"]
Outcome = Literal["SUCCEEDED", "FAILED"]


# ---------------------------------------------------------------- shared parts
class Identifier(ApiModel):
    """Identifier of a company, such as `VAT_ID` or `COMMERCIAL_REG_NUMBER` (README 2, 6.5)."""
    type: str = Field(min_length=1, description="identifier type from the reference data, such as VAT_ID")
    value: str = Field(min_length=1)


class Address(ApiModel):
    """Address as the CSP takes it; C12 maps it from the C3-M1 address (flows.yaml, company-core-data)."""
    street_address: str | None = None
    postal_code: str | None = None
    locality: str | None = None
    country: str | None = None


# ---------------------------------------------------------------- step inputs (README 8)
class StepInput(StepRequest):
    """Every step input of C3-M2 (FRAMEWORK 4.4): `processId`, `stepRunId` and the company."""
    company_id: Uuid


class RegisterCompanyInput(StepInput):
    """README 8.1. At least `ebwoid`, `euid` or an entry in `identifiers` (README 6.5); the step
    checks this and answers 400 `validation`."""
    legal_name: str = Field(min_length=1)
    country: CountryCode = Field(examples=["DE"])
    ebwoid: str | None = Field(default=None, examples=["EBWOID-DE-0000000001"])
    euid: str | None = Field(default=None, examples=["DEXX001T.HRB100001"])
    identifiers: list[Identifier] | None = None
    address: Address | None = None


class TransferCompanyInput(StepInput):
    """README 8.2. `bpn` from `find-companies`."""
    bpn: str = Field(min_length=1, examples=["BPNL00000000002B"])
    ebwoid: str | None = None
    euid: str | None = None
    identifiers: list[Identifier] | None = None


class RegisterDidInput(StepInput):
    """README 8.3."""
    did: str = Field(min_length=1, examples=["did:web:wallet.example.org:BPNL00000000OSPA"])


class UpdateCompanyInput(StepInput):
    """README 8.4."""
    legal_name: str = Field(min_length=1)
    euid: str | None = None
    address: Address | None = None


class ConnectorInput(StepInput):
    """README 8.6, `deregister-connector`. `companyId` is the host company of the connector."""
    connector_id: Uuid


class RegisterConnectorInput(ConnectorInput):
    """README 8.6, `register-connector`."""
    endpoint_url: str = Field(pattern=r"^https://", description="address of the connector (DSP endpoint), HTTPS",
                              examples=["https://edc.beispiel-maschinenbau.example/dsp"])


# ---------------------------------------------------------------- step result (FRAMEWORK 4.4)
class StepResultData(ApiModel):
    """Fields later steps read, for example `steps.register-company.bpn` in flows.yaml."""
    bpn: str | None = None
    did: str | None = None
    connector_id: Uuid | None = None


class StepResult(models.StepResult[StepResultData]):
    """Answer of every step: DONE with the result, or RUNNING until the completing event."""


# ---------------------------------------------------------------- other operations
class CspRegistration(ApiModel):
    """README 7.1: the status of a company at the CSP."""
    company_id: Uuid
    bpn: str | None = None
    status: RegistrationStatus
    failure_reason: str | None = None
    did: str | None = None
    membership: Membership
    registered_at: str | None = Field(default=None, description="date-time")
    updated_at: str | None = Field(default=None, description="date-time")


class CspCompanyMatch(ApiModel):
    """README 9: one match of the duplicate check."""
    bpn: str
    legal_name: str
    country: str
    matched_by: Literal["EBWOID", "EUID", "IDENTIFIER", "NAME"]
    home_osp_id: Uuid
    home_osp_name: str | None = None
    home_is_this_osp: bool
    member_active: bool | None = None


class CspNotification(ApiModel):
    """README 7.2: notification from the CSP. `operationId` and `outcome` with `OperationCompleted`."""
    notification_id: str = Field(min_length=1)
    type: NotificationType
    bpn: str | None = None
    operation_id: str | None = None
    outcome: Outcome | None = None
    reason: str | None = None


def invalid_fields(model: type[ApiModel], data: object) -> str | None:
    """The fields of `data` that `model` rejects, comma-separated, or None when `data` is valid."""
    try:
        model.model_validate(data)
    except ValidationError as e:
        return ", ".join(sorted({".".join(str(x) for x in err["loc"]) for err in e.errors()}))
    return None

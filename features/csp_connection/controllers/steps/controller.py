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
"""The steps of the CSP connection in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from features.csp_connection import interface
from features.csp_connection.interface import StepReply
from features.csp_connection.models.schemas import (
    ConnectorInput,
    RegisterCompanyInput,
    RegisterConnectorInput,
    RegisterDidInput,
    StepInput,
    StepResult,
    TransferCompanyInput,
    UpdateCompanyInput,
)
from portal_common.routing import Controller, Permission

controller = Controller("CSP Connection: Steps")


@controller.post("/register-company", operation_id="stepRegisterCompany",
                 summary="Register a company with the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def register_company(body: RegisterCompanyInput, _: dict = Permission) -> StepReply:
    """README 8.1. DONE with `bpn`, or RUNNING until `CompanyRegisteredAtCsp`."""
    return interface.register_company(body.to_json())


@controller.post("/transfer-company", operation_id="stepTransferCompany",
                 summary="Transfer a company to this OSP",
                 response_model=StepResult, response_model_exclude_none=True)
def transfer_company(body: TransferCompanyInput, _: dict = Permission) -> StepReply:
    """README 8.2. The company moves to this OSP; answers as register-company."""
    return interface.transfer_company(body.to_json())


@controller.post("/register-did", operation_id="stepRegisterDid",
                 summary="Enter the DID in the directory BPN → DID",
                 response_model=StepResult, response_model_exclude_none=True)
def register_did(body: RegisterDidInput, _: dict = Permission) -> StepReply:
    """README 8.3. Needs status REGISTERED."""
    return interface.register_did(body.to_json())


@controller.post("/update-company", operation_id="stepUpdateCompany",
                 summary="Pass changed core data to the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def update_company(body: UpdateCompanyInput, _: dict = Permission) -> StepReply:
    """README 8.4. Needs status REGISTERED."""
    return interface.update_company(body.to_json())


@controller.post("/register-membership", operation_id="stepRegisterMembership",
                 summary="Register the membership at the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def register_membership(body: StepInput, _: dict = Permission) -> StepReply:
    """README 8.5. Needs status REGISTERED; calls the CSP only on a change."""
    return interface.register_membership(body.to_json())


@controller.post("/deregister-membership", operation_id="stepDeregisterMembership",
                 summary="Deregister the membership at the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def deregister_membership(body: StepInput, _: dict = Permission) -> StepReply:
    """README 8.5. After `CompanyTransferredAway`: DONE without a call."""
    return interface.deregister_membership(body.to_json())


@controller.post("/register-connector", operation_id="stepRegisterConnector",
                 summary="Enter a connector in the discovery of the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def register_connector(body: RegisterConnectorInput, _: dict = Permission) -> StepReply:
    """README 8.6. Calls the CSP only for a new connector or a new address."""
    return interface.register_connector(body.to_json())


@controller.post("/deregister-connector", operation_id="stepDeregisterConnector",
                 summary="Remove a connector from the discovery of the CSP",
                 response_model=StepResult, response_model_exclude_none=True)
def deregister_connector(body: ConnectorInput, _: dict = Permission) -> StepReply:
    """README 8.6. Unknown or already removed: DONE without a call."""
    return interface.deregister_connector(body.to_json())

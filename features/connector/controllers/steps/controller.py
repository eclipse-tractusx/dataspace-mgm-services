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
"""The steps of the connectors in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from features.connector import interface
from features.connector.models import ConnectorIds, DeactivateSubscriptionConnectorsInput, UnlinkTechnicalUserInput
from portal_common.models import StepResult
from portal_common.routing import Controller, Permission

controller = Controller("Connector: Process Steps and Queries")


@controller.post("/deactivate-subscription-connectors",
                 operation_id="stepDeactivateSubscriptionConnectors",
                 summary="Deactivate the connector of an ended subscription",
                 response_model=StepResult[ConnectorIds])
def deactivate_subscription_connectors(body: DeactivateSubscriptionConnectorsInput, _: dict = Permission) -> dict:
    return interface.deactivate_subscription_connectors(body)


@controller.post("/unlink-technical-user",
                 operation_id="stepUnlinkTechnicalUser",
                 summary="Remove the link to a deleted technical user",
                 response_model=StepResult[ConnectorIds])
def unlink_technical_user(body: UnlinkTechnicalUserInput, _: dict = Permission) -> dict:
    return interface.unlink_technical_user(body)

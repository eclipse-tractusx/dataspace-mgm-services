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
"""A new secret for a subscription account (README 9.2)."""
from __future__ import annotations

from fastapi import Body

from features.technical_user import interface
from features.technical_user.models import validation
from features.technical_user.models.responses import WIRE, Credentials
from features.technical_user.models.schemas import SubscriptionCredentialsRequest
from portal_common.routing import Controller, Permission

controller = Controller("Technical User: Process Steps and Queries")


@controller.post("/rotate", summary="Rotate a subscription account's secret", response_model=Credentials, **WIRE)
def rotate_subscription_credentials(id: str, body: dict = Body(...), _: dict = Permission) -> dict:
    request = validation.parse(SubscriptionCredentialsRequest, body)   # undeclared fields (even `id`) are a 400
    return interface.rotate_subscription_credentials(id=id, offerSubscriptionId=request.offer_subscription_id)

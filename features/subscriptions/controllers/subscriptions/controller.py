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
"""Subscriptions of the app path of FRAMEWORK 5.8: subscribe, read, start setup, activate."""
from __future__ import annotations

from features.subscriptions import interface
from features.subscriptions.models.requests import StartSetupRequest, SubscribeRequest
from features.subscriptions.models.subscription import Subscription
from portal_common.routing import Controller, Permission

controller = Controller("Subscriptions: Subscriptions")


@controller.post("", status_code=201, response_model=Subscription)
def subscribe(body: SubscribeRequest, claims: dict = Permission) -> Subscription:
    return interface.subscribe(claims.get("company_id"), body)


@controller.get("/{offerSubscriptionId}", response_model=Subscription)
def get_subscription(offerSubscriptionId: str, claims: dict = Permission) -> Subscription:
    return interface.get_subscription(claims.get("company_id"), offerSubscriptionId)


@controller.post("/{offerSubscriptionId}/start-setup", status_code=202, response_model=Subscription)
def start_setup(offerSubscriptionId: str, body: StartSetupRequest | None = None,
                claims: dict = Permission) -> Subscription:
    return interface.start_setup(claims.get("company_id"), offerSubscriptionId, body or StartSetupRequest())


@controller.post("/{offerSubscriptionId}/activate", response_model=Subscription)
def activate(offerSubscriptionId: str, claims: dict = Permission) -> Subscription:
    return interface.activate(claims.get("company_id"), offerSubscriptionId)

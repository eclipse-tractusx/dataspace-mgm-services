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
"""In-process contract of the subscriptions (call convention, AGENTS.md): the steps `notify-provider` and
`send-activation-callback` (client ID of the instance and a rotated secret of the technical user to the provider's
`callbackUrl`, C10-M1 11.2) and the queries of section 9 under their convention names, plus the operations of people,
which only the controllers call. Other modules and Process Orchestration import only from here and get JSON
(camelCase dicts); the logic lives in `services/`."""
from __future__ import annotations

from features.subscriptions import services
from features.subscriptions.models.provider_configuration import ProviderConfiguration, ProviderConfigurationInput
from features.subscriptions.models.requests import (
    ActivationCallbackStep,
    StartSetupRequest,
    SubscribeRequest,
    SubscriptionStep,
)
from features.subscriptions.models.subscription import MODULE, Subscription
from features.subscriptions.services import reset
from portal_common import standin

__all__ = ["MODULE", "activate", "find_subscriptions", "get_subscription", "get_subscription_internal",
           "notify_provider", "put_provider_configuration", "reset", "send_activation_callback", "start_setup",
           "subscribe"]


# -- steps for Process Orchestration: input = JSON body incl. processId and stepRunId ---------------
def notify_provider(input: dict | SubscriptionStep) -> dict:
    return services.notify_provider(input)


def send_activation_callback(input: dict | ActivationCallbackStep) -> dict:
    return services.send_activation_callback(input)


# -- queries (section 9) -------------------------------------------------------------------------------
def find_subscriptions(*, customerCompanyId: str | None = None, offerId: str | None = None,
                       status: list[str] | str | None = None, **_other: object) -> list[dict]:
    """9.1: `SubscriptionRef` of the matching subscriptions; other parameters are ignored."""
    found = services.find_subscriptions(customerCompanyId=customerCompanyId, offerId=offerId, status=status)
    return [s.model_dump(mode="json") for s in found]


def get_subscription_internal(*, offerSubscriptionId: str) -> dict:
    """9.2: `SubscriptionInternal`."""
    return services.get_subscription_internal(offerSubscriptionId=offerSubscriptionId).model_dump(mode="json")


# -- operations of people (section 7), called by the controllers with the company of the token -----------
def subscribe(company_id: str | None, body: SubscribeRequest) -> Subscription:
    return services.subscribe(company_id, body)


def get_subscription(company_id: str | None, offer_subscription_id: str) -> Subscription:
    return services.get_subscription(company_id, offer_subscription_id)


def start_setup(company_id: str | None, offer_subscription_id: str, body: StartSetupRequest) -> Subscription:
    return services.start_setup(company_id, offer_subscription_id, body)


def activate(company_id: str | None, offer_subscription_id: str) -> Subscription:
    return services.activate(company_id, offer_subscription_id)


def put_provider_configuration(company_id: str | None, body: ProviderConfigurationInput) -> ProviderConfiguration:
    return services.put_provider_configuration(company_id, body)


__getattr__ = standin.missing_interface(MODULE)   # steps and queries not implemented yet: stand-in

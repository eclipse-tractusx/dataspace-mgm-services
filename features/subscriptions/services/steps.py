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
"""The steps of the subscriptions in the flows of Process Orchestration (section 8): `notify-provider` and
`send-activation-callback` (client ID of the instance and a rotated secret of the technical user to the provider's
`callbackUrl`, 11.2)."""
from __future__ import annotations

from features.subscriptions.managers import (
    neighbour_client,
    provider_client,
    provider_configuration_repository,
    subscription_repository,
)
from features.subscriptions.models.errors import problem
from features.subscriptions.models.requests import ActivationCallbackStep, SubscriptionStep
from features.subscriptions.models.subscription import SubscriptionInternal
from features.subscriptions.models.validation import parse
from portal_common.models import StepResult


def _subscription(step: SubscriptionStep) -> SubscriptionInternal:
    s = subscription_repository.get(step.offer_subscription_id)
    if not s:
        raise problem(404, "not-found", retryable=False)
    return s


def _done(step: SubscriptionStep) -> dict:
    return StepResult[dict].done(step, {}).to_json()


def notify_provider(input: dict | SubscriptionStep) -> dict:
    step = parse(SubscriptionStep, input)
    s = _subscription(step)
    customer = neighbour_client.query_company(s.customer_company_id)
    provider_client.call(s.provider_company_id, "setup", {
        "offerSubscriptionId": s.offer_subscription_id, "offerId": s.offer_id,
        "customerCompanyId": s.customer_company_id,
        "customerName": customer.get("name"), "customerCountry": (customer.get("address") or {}).get("countryCode"),
        "setupExpected": s.offer_type == "APP"})
    return _done(step)


def send_activation_callback(input: dict | ActivationCallbackStep) -> dict:
    step = parse(ActivationCallbackStep, input)
    s = _subscription(step)
    config = provider_configuration_repository.get(s.provider_company_id)
    if not config or not config.callback_url:
        return _done(step)    # without a callbackUrl: nothing to do
    technical_user = None
    for account in step.technical_users:   # one rotation per account, the callback names the last one (11.2)
        r = neighbour_client.rotate_subscription_credentials(account.technical_user_id, s.offer_subscription_id)
        technical_user = {"clientId": r["iamClientId"], "clientSecret": r["secret"]}
    provider_client.call(s.provider_company_id, "callback", {
        "offerSubscriptionId": s.offer_subscription_id, "instanceUrl": s.instance_url, "clientId": step.client_id,
        "technicalUser": technical_user})
    return _done(step)

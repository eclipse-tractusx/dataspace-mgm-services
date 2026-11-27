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
"""Subscriptions of the app path of FRAMEWORK 5.8: subscribe, start setup, activate (refused while the setup process
at C12-M1 is `RUNNING` or `FAILED`, 6.3). A subscription is visible to its customer and to the provider of the
offer; another company gets 404, and only the provider may start the setup or activate (403)."""
from __future__ import annotations

import uuid

from features.subscriptions.managers import neighbour_client, subscription_repository
from features.subscriptions.models.errors import problem
from features.subscriptions.models.requests import StartSetupRequest, SubscribeRequest
from features.subscriptions.models.subscription import MODULE, SetupStatus, Subscription, SubscriptionInternal
from portal_common import events

_ACTIVATION_REFUSED: dict[str, str] = {"RUNNING": "setup-not-finished", "FAILED": "setup-failed"}


def _visible(company_id: str | None, sid: str, provider_only: bool = False) -> SubscriptionInternal:
    s = subscription_repository.get(sid)
    if not s or company_id not in (s.provider_company_id, s.customer_company_id):
        raise problem(404, "not-found")
    if provider_only and company_id != s.provider_company_id:
        raise problem(403, "forbidden")
    return s


def _setup_status(sid: str) -> SetupStatus | None:
    """Status of the `subscription-setup` process of the subscription at C12-M1, None without one."""
    procs = neighbour_client.find_processes_of_subscription(sid)
    return next((p["status"] for p in procs if p["flowKey"] == "subscription-setup"), None)


def _view(s: SubscriptionInternal, setup_status: SetupStatus | None = None) -> Subscription:
    return Subscription(**s.model_dump(), setup_status=setup_status)


def subscribe(company_id: str | None, body: SubscribeRequest) -> Subscription:
    if not company_id:
        raise problem(403, "forbidden", detail="the token names no company")
    offer = neighbour_client.get_offer_internal(body.offer_id)
    if not offer or offer["status"] != "ACTIVE":
        raise problem(409, "offer-not-active")
    if offer["providerCompanyId"] == company_id:
        raise problem(409, "own-offer")
    s = SubscriptionInternal(offer_subscription_id=str(uuid.uuid4()), offer_id=offer["offerId"],
                             offer_type=offer["offerType"], instance_kind=offer.get("instanceKind"),
                             customer_company_id=company_id, provider_company_id=offer["providerCompanyId"],
                             status="REQUESTED")
    subscription_repository.save(s)
    events.publish(MODULE, "SubscriptionRequested", s.event_data())
    return _view(s)


def get_subscription(company_id: str | None, sid: str) -> Subscription:
    s = _visible(company_id, sid)
    return _view(s, _setup_status(sid))


def start_setup(company_id: str | None, sid: str, body: StartSetupRequest) -> Subscription:
    s = _visible(company_id, sid, provider_only=True)
    if s.status != "REQUESTED":
        raise problem(409, "invalid-state")
    s.status, s.instance_url = "PENDING", body.instance_url
    subscription_repository.save(s)
    events.publish(MODULE, "SubscriptionSetupStarted", s.event_data(instanceUrl=s.instance_url))
    return _view(s)


def activate(company_id: str | None, sid: str) -> Subscription:
    s = _visible(company_id, sid, provider_only=True)
    if s.status != "PENDING":
        raise problem(409, "invalid-state")
    status = _setup_status(sid)
    refused = _ACTIVATION_REFUSED.get(status) if status else None
    if refused:
        raise problem(409, refused)
    s.status = "ACTIVE"
    subscription_repository.save(s)
    events.publish(MODULE, "SubscriptionActivated", s.event_data(instanceKind=s.instance_kind))
    return _view(s)

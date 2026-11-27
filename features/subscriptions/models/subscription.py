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
"""The spec id, the value sets and the subscription models of C10-M1 (`openapi.yaml`, sections 6, 9 and 10).

The stand-in keeps its own status `REQUESTED` before the setup (the spec starts with `PENDING`, OPEN-QUESTIONS 3).
"""
from __future__ import annotations

from typing import Literal

from portal_common.models import ApiModel, Uuid

MODULE = "c10-m1"

OfferType = Literal["APP", "SERVICE"]
InstanceKind = Literal["SINGLE", "MULTI"]
SubscriptionStatus = Literal["REQUESTED", "PENDING", "ACTIVE"]
SetupStatus = Literal["RUNNING", "WAITING", "FAILED", "COMPLETED", "ENDED"]


class SubscriptionRef(ApiModel):
    """9.1: what other modules need to find a subscription."""

    offer_subscription_id: Uuid
    offer_id: Uuid
    customer_company_id: Uuid
    status: SubscriptionStatus


class SubscriptionInternal(SubscriptionRef):
    """9.2: the subscription as other modules see it; also the stored record of the stand-in."""

    offer_type: OfferType
    instance_kind: InstanceKind | None = None
    provider_company_id: Uuid
    instance_url: str | None = None

    def ref(self) -> SubscriptionRef:
        return SubscriptionRef.model_validate(self.model_dump(include=set(SubscriptionRef.model_fields)))

    def event_data(self, **extra: object) -> dict:
        """Content of the subscription events (section 10): the subscription's identity plus `extra`."""
        return self.model_dump(mode="json", include={"offer_subscription_id", "offer_id", "offer_type",
                                                     "customer_company_id", "provider_company_id"}) | extra


class Subscription(SubscriptionInternal):
    """7.3: the subscription for its customer and its provider, with the status of the setup process at C12-M1."""

    setup_status: SetupStatus | None = None

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
"""Request bodies and step inputs of C10-M1 (`openapi.yaml`): unknown fields are refused, as the spec says."""
from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from portal_common.models import ApiModel, RequestBody, StepRequest, Uuid

INSTANCE_URL = r"^https://[^#]+$"


class AgreementConsent(RequestBody):
    agreement_id: Uuid
    consent: Literal["ACTIVE", "INACTIVE"]


class SubscribeRequest(RequestBody):
    """7.2: subscribe to an offer."""

    offer_id: Uuid
    agreement_consents: list[AgreementConsent]


class StartSetupRequest(RequestBody):
    """7.5: the provider starts the setup, for a multi-instance app with the URL of the instance."""

    instance_url: str | None = Field(default=None, pattern=INSTANCE_URL)


class SubscriptionStep(StepRequest):
    """8.1: input of `notify-provider`."""

    offer_subscription_id: Uuid


class TechnicalUserAccount(ApiModel):
    """One entry of the result `accounts` of C2-M3 `create-for-subscription`; other fields are kept."""

    model_config = ConfigDict(extra="allow")

    technical_user_id: str


class ActivationCallbackStep(SubscriptionStep):
    """8.2: input of `send-activation-callback`."""

    client_id: str | None = None
    technical_users: list[TechnicalUserAccount] = []

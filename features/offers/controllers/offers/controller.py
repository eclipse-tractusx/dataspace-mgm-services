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
"""The own offers of a provider (README 6.1, 6.2), scope `company`: create, read, submit."""
from __future__ import annotations

from features.offers import interface
from features.offers.models import MODULE, Offer, OfferInput
from portal_common.routing import Controller, Permission, company_scope

controller = Controller("Offers: Offers")


@controller.post("", status_code=201, response_model=Offer, summary="Create an offer (company role checked at C3-M1)")
def create_offer(body: OfferInput, claims: dict = Permission) -> Offer:
    return interface.create_offer(company_id=claims.get("company_id"), body=body)


@controller.get("/{offerId}", response_model=Offer, summary="An own offer")
def get_own_offer(offerId: str, claims: dict = Permission) -> Offer:
    company_scope(MODULE, claims, interface.provider_of(offerId))
    return interface.get_offer(offerId)


@controller.post("/{offerId}/submit", response_model=Offer, summary="Submit an offer for review")
def submit_offer(offerId: str, claims: dict = Permission) -> Offer:
    company_scope(MODULE, claims, interface.provider_of(offerId))
    return interface.submit_offer(offerId)

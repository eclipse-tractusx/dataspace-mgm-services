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
"""Stand-in of C8-M1 Offers, hackathon core path: a provider creates an offer (company role checked
at C3-M1), sets roles and the technical user profile, submits; OSP staff approve (`OfferApproved`);
`get_offer_internal` serves the lookup `offer` of Process Orchestration and Subscriptions.
"""
from __future__ import annotations

import uuid

from features.offers.managers import neighbour_client, offer_repository
from features.offers.models import (
    MODULE,
    ROLE_FOR,
    AppRole,
    Offer,
    OfferEvent,
    OfferInput,
    OfferInternal,
    TechnicalUserProfile,
    problem,
)
from portal_common import events


def provider_of(offer_id: str) -> str | None:
    """The provider company of an offer, for the scope `company` of the controllers; None if unknown."""
    offer = offer_repository.get(offer_id)
    return offer.provider_company_id if offer else None


def get_offer(offer_id: str) -> Offer:
    offer = offer_repository.get(offer_id)
    if offer is None:
        raise problem(404, "not-found")
    return offer


def create_offer(*, company_id: str | None, body: OfferInput) -> Offer:
    """A draft; the provider company needs the company role of the offer type at C3-M1 (README 6.2)."""
    role = ROLE_FOR[body.offer_type]
    company = neighbour_client.query_company(company_id) if company_id else None
    if not company_id or not company or role not in company.get("companyRoles", []):
        raise problem(403, "company-role-missing", detail=f"company role {role} missing")
    is_app = body.offer_type == "APP"
    return offer_repository.save(Offer(
        offer_id=str(uuid.uuid4()), status="DRAFT", offer_type=body.offer_type, name=body.name,
        provider_company_id=company_id, instance_kind=body.instance_kind if is_app else None,
        instance_url=body.instance_url))


def replace_planned_roles(offer_id: str, roles: list[AppRole]) -> list[AppRole]:
    offer = get_offer(offer_id)
    offer.roles = roles
    offer_repository.save(offer)
    return offer.roles


def put_technical_user_profile(offer_id: str, profile: TechnicalUserProfile) -> TechnicalUserProfile:
    offer = get_offer(offer_id)
    offer.technical_user_profile = profile
    offer_repository.save(offer)
    return profile


def submit_offer(offer_id: str) -> Offer:
    """DRAFT -> IN_REVIEW; an app needs planned roles."""
    offer = get_offer(offer_id)
    if offer.status != "DRAFT":
        raise problem(409, "invalid-state")
    if offer.offer_type == "APP" and not offer.roles:
        raise problem(409, "incomplete", detail="an app needs roles")
    offer.status = "IN_REVIEW"
    return offer_repository.save(offer)


def approve_offer(offer_id: str) -> Offer:
    """IN_REVIEW -> ACTIVE and `OfferApproved`, which starts the flow `app-approval` of Process Orchestration."""
    offer = get_offer(offer_id)
    if offer.status != "IN_REVIEW":
        raise problem(409, "invalid-state")
    offer.status = "ACTIVE"
    offer_repository.save(offer)
    event = OfferEvent(offer_id=offer.offer_id, offer_type=offer.offer_type,
                       provider_company_id=offer.provider_company_id)
    events.publish(MODULE, "OfferApproved", event.to_json())
    return offer


def get_offer_internal(offer_id: str) -> OfferInternal:
    """README 9.1: the offer with `hasTechnicalUserProfile`."""
    offer = get_offer(offer_id)
    has_profile = offer.technical_user_profile is not None
    return OfferInternal(**offer.model_dump(by_alias=False), has_technical_user_profile=has_profile)

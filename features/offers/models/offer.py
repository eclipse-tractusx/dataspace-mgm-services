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
"""Pydantic models of the offers, with the field names of `openapi.yaml` in JSON (`portal_common.models.ApiModel`).

The stand-in keeps only the fields of the hackathon core path; further fields of `OfferInput` are accepted and
ignored, as the schema has no `additionalProperties: false`.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from portal_common.models import ApiModel, Uuid

OfferType = Literal["APP", "SERVICE"]
OfferStatus = Literal["DRAFT", "IN_REVIEW", "ACTIVE"]    # stand-in subset (OPEN-QUESTIONS 2)
InstanceKind = Literal["SINGLE", "MULTI"]


class OfferInput(ApiModel):
    """Body of `POST /offers` (schema `OfferInput`), the fields the stand-in stores."""

    offer_type: OfferType
    name: str = Field(min_length=1)
    instance_kind: InstanceKind | None = "MULTI"   # only kept for an app
    instance_url: str | None = None


class RoleDescription(ApiModel):
    lang: str
    text: str


class AppRole(ApiModel):
    """A planned app role (schema `AppRole`, the format of C2-M2 `create-client-template`)."""

    name: str
    descriptions: list[RoleDescription] = []


class ProfileRole(ApiModel):
    name: str


class TechnicalUserProfile(ApiModel):
    """Name and roles of the technical user a subscription creates (schema `TechnicalUserProfile`)."""

    name: str = Field(min_length=1)
    roles: list[ProfileRole] = Field(min_length=1)


class Offer(ApiModel):
    """An offer as the provider and OSP staff see it (schema `Offer`, the fields of the stand-in)."""

    offer_id: Uuid
    status: OfferStatus
    offer_type: OfferType
    name: str
    provider_company_id: str
    instance_kind: InstanceKind | None = None
    instance_url: str | None = None
    roles: list[AppRole] = []
    technical_user_profile: TechnicalUserProfile | None = None
    agreements: list[dict] = []


class OfferInternal(Offer):
    """Answer of the query `getOfferInternal` (schema `OfferInternal`)."""

    has_technical_user_profile: bool


class OfferEvent(ApiModel):
    """Content of `OfferApproved` (README 10)."""

    offer_id: Uuid
    offer_type: OfferType
    provider_company_id: str

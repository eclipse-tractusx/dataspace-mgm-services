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
"""Tables of the offers in the feature's own database (`portal_common.database`, F17).

A row holds the fields of the API model `Offer`; `Offer.model_validate(row, from_attributes=True)` turns it into
the model. Roles, the technical user profile and agreements belong to one offer and are only read with it, so
they are JSON columns instead of tables of their own.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from features.offers.models import MODULE
from portal_common import database

if TYPE_CHECKING:   # for mypy the plain SQLModel base; at run time the feature's own registry and MetaData
    Table = SQLModel
else:
    Table = database.table_base(MODULE)


class OfferRow(Table, table=True):
    __tablename__ = "offer"

    offer_id: str = Field(primary_key=True)
    status: str = Field(index=True)
    offer_type: str
    name: str
    provider_company_id: str = Field(index=True)
    instance_kind: str | None = None
    instance_url: str | None = None
    roles: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    technical_user_profile: dict | None = Field(default=None, sa_column=Column(JSON))
    agreements: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False))

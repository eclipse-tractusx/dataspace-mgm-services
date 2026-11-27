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
"""The tables of the subscriptions in their own database (F17, `portal_common.database`)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field

from features.subscriptions.models.subscription import MODULE
from portal_common import database

if TYPE_CHECKING:   # the type checker sees the plain SQLModel base; at run time it is the feature's own registry
    from sqlmodel import SQLModel as Table
else:
    Table = database.table_base(MODULE)


class SubscriptionRow(Table, table=True):
    """One subscription; looked up by id, by customer company and by offer (9.1)."""

    __tablename__ = "subscription"

    offer_subscription_id: str = Field(primary_key=True)
    offer_id: str = Field(index=True)
    offer_type: str
    instance_kind: str | None = None
    customer_company_id: str = Field(index=True)
    provider_company_id: str
    status: str
    instance_url: str | None = None


class ProviderConfigurationRow(Table, table=True):
    """The provider configuration of one company, with its secret."""

    __tablename__ = "provider_configuration"

    company_id: str = Field(primary_key=True)
    setup_url: str
    callback_url: str
    token_url: str
    client_id: str
    client_secret: str
    updated_at: datetime

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
"""The subscriptions in the feature's database: the only code that opens a session for them."""
from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import col, select

from features.subscriptions.models.subscription import MODULE, SubscriptionInternal
from features.subscriptions.models.tables import SubscriptionRow
from portal_common import database


def _model(row: SubscriptionRow) -> SubscriptionInternal:
    return SubscriptionInternal.model_validate(row, from_attributes=True)


def save(subscription: SubscriptionInternal) -> None:
    """Insert or replace the subscription."""
    with database.session(MODULE) as session:
        session.merge(SubscriptionRow(**subscription.model_dump(by_alias=False)))


def get(offer_subscription_id: str) -> SubscriptionInternal | None:
    with database.session(MODULE) as session:
        row = session.get(SubscriptionRow, offer_subscription_id)
        return _model(row) if row else None


def find(customer_company_id: str | None, offer_id: str | None, statuses: Iterable[str]) -> list[SubscriptionInternal]:
    """The subscriptions that match every given filter; a filter left empty matches all."""
    query = select(SubscriptionRow)
    if customer_company_id:
        query = query.where(SubscriptionRow.customer_company_id == customer_company_id)
    if offer_id:
        query = query.where(SubscriptionRow.offer_id == offer_id)
    if statuses := list(statuses):
        query = query.where(col(SubscriptionRow.status).in_(statuses))
    with database.session(MODULE) as session:
        return [_model(row) for row in session.exec(query)]

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
"""The offers in the feature's database (`models/tables.py`); the only code that opens its session."""
from __future__ import annotations

from features.offers.models import MODULE, Offer
from features.offers.models.tables import OfferRow
from portal_common import database


def get(offer_id: str) -> Offer | None:
    """One offer by its primary key."""
    with database.session(MODULE) as session:
        row = session.get(OfferRow, offer_id)
        return Offer.model_validate(row, from_attributes=True) if row else None


def save(offer: Offer) -> Offer:
    """Insert or update the whole offer."""
    with database.session(MODULE) as session:
        session.merge(OfferRow(**offer.model_dump(by_alias=False)))
    return offer

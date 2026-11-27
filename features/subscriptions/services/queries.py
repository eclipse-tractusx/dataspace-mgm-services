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
"""The queries of the subscriptions for other modules (section 9)."""
from __future__ import annotations

from features.subscriptions.managers import subscription_repository
from features.subscriptions.models.errors import problem
from features.subscriptions.models.subscription import SubscriptionInternal, SubscriptionRef


def find_subscriptions(*, customerCompanyId: str | None = None, offerId: str | None = None,
                       status: list[str] | str | None = None) -> list[SubscriptionRef]:
    """9.1: the matching subscriptions, filtered in the database (indexed columns)."""
    statuses = [status] if isinstance(status, str) else status or []
    return [s.ref() for s in subscription_repository.find(customerCompanyId, offerId, statuses)]


def get_subscription_internal(*, offerSubscriptionId: str) -> SubscriptionInternal:
    """9.2: one subscription by id."""
    s = subscription_repository.get(offerSubscriptionId)
    if not s:
        raise problem(404, "not-found")
    return s

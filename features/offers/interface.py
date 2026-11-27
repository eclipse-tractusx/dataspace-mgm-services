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
"""In-process contract of the offers (call convention, AGENTS.md): the query `getOfferInternal` serves the lookup
`offer` of Process Orchestration and Subscriptions, and the operations of people, which only the controllers call.
Other services and Process Orchestration import only from here; the logic lives in `services/`."""
from __future__ import annotations

from features.offers import services
from features.offers.models import MODULE
from features.offers.services import (
    approve_offer,
    create_offer,
    get_offer,
    provider_of,
    put_technical_user_profile,
    replace_planned_roles,
    submit_offer,
)
from portal_common import database, standin

__all__ = ["MODULE", "approve_offer", "create_offer", "get_offer", "get_offer_internal", "provider_of",
           "put_technical_user_profile", "replace_planned_roles", "reset", "submit_offer"]


def reset() -> None:
    database.reset_tables(MODULE)


def get_offer_internal(*, offerId: str) -> dict:
    """README 9.1, as JSON (the in-process answer equals the HTTP one)."""
    return services.get_offer_internal(offerId).model_dump(mode="json", by_alias=True)


__getattr__ = standin.missing_interface(MODULE)   # steps and queries not implemented yet: stand-in

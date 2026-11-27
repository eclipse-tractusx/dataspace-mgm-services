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
"""Offers (spec C8-M1): apps and services of providers, approved by OSP staff. Stand-in of the hackathon core
path: a provider creates an offer (company role checked at C3-M1), sets roles and the technical user profile,
submits; OSP staff approve (`OfferApproved`); `GET /internal/offers/{offerId}` serves the lookup `offer` of
Process Orchestration and Subscriptions. Every other operation of the spec answers from the scaffold fallback.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks `on_startup()`
(creates the tables) and `reset()` (empties them).
The HTTP API is `features.offers.router.router`.
"""
from __future__ import annotations

from features.offers.models import MODULE
from portal_common import database

NAME = "offers"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def on_startup() -> None:
    database.create_tables(MODULE)


def reset() -> None:
    database.reset_tables(MODULE)

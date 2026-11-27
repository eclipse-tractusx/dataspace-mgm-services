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
#  Assisted-By: GitHub Copilot CLI (Claude)
#################################################################################
"""Process Orchestration as the event hub of the installation (ADR-0006).

Every CloudEvent of the installation reaches Process Orchestration: in its own runtime through the relay,
from the other runtimes through the event inbox (`POST /api/v1/events/inbox`), because their forwarder posts
every published event to the address of C12-M1 (`portal_common.event_forwarder`). The hub

1. routes the event on to the runtimes of the subscribing modules (`route`), so that events between features
   in different runtimes still arrive, and
2. hands it to the engine, which starts, continues or ends processes (README 6.5).

Routing rules: no delivery to a subscriber in this runtime (the relay delivered it already), to a stand-in, to
the runtime of the publisher (its relay delivered it there) or twice to the same runtime. The receiving inbox
deduplicates by `source` and `id` and never forwards again, so a misconfigured second hub cannot loop.
In the modular monolith every subscriber is in-process: nothing leaves the process.
"""
from __future__ import annotations

import logging

from features.process_orchestration.managers import event_routes
from features.process_orchestration.models.errors import MODULE

log = logging.getLogger(MODULE)


def publisher(event: dict) -> str:
    """Spec id of the module that published `event` (`source` `urn:<module>`, FRAMEWORK 6)."""
    return str(event.get("source", "")).removeprefix("urn:")


def destinations(event: dict) -> list[str]:
    """Base addresses of the runtimes `event` still has to reach, in the order of the subscribers."""
    origin = event_routes.remote_address(publisher(event)) if publisher(event) else ""
    out: list[str] = []
    for module in event_routes.subscribers():
        address = event_routes.remote_address(module)
        if address and address != origin and address not in out:
            out.append(address)
    return out


def route(event: dict) -> list[str]:
    """Sends `event` on to `destinations(event)`; returns them."""
    addresses = destinations(event)
    if addresses:
        log.debug("event hub: %s %s from %s to %s", event.get("type"), event.get("id"), event.get("source"), addresses)
        event_routes.deliver(event, addresses)
    return addresses

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
"""Addresses and delivery of the event hub (ADR-0006): where the events of the installation go from here.

A module is a subscriber of the event bus when its feature index has `on_event(event)`
(`portal_common.layout.subscribers`). Its runtime is found with the neighbour rule of FRAMEWORK 4.7
(`<MODULE>_URL`, `MODULE_URLS`, `portal_common.neighbours`): `in-process` means the relay of this runtime
already delivers to it, an empty address means a stand-in that receives nothing, otherwise the HTTP address of
its runtime. Delivery goes through `portal_common.event_forwarder` (inbox `POST /api/v1/events/inbox`, service
token of the publishing module, retries, no loops).
"""
from __future__ import annotations

from features.process_orchestration.models.errors import MODULE
from portal_common import event_forwarder, layout, neighbours


def subscribers() -> list[str]:
    """Spec ids of the modules that subscribe to the event bus, without Process Orchestration itself."""
    return [mid for mid in layout.subscribers() if mid != MODULE]


def remote_address(module: str) -> str:
    """HTTP address of the runtime that serves `module`; empty when it runs in this process or is a stand-in."""
    if neighbours.in_process(module) or neighbours.is_standin(module):
        return ""
    return neighbours.address(module)


def deliver(event: dict, addresses: list[str]) -> None:
    """Hands `event` to the inboxes of `addresses`, off the request path (`event_forwarder.FORWARDER`)."""
    event_forwarder.FORWARDER.dispatch(event, addresses)

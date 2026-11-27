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
"""Process Orchestration (spec C12-M1): runs the flows of `flows.yaml`; every step and lookup is a call of
another module, addressed by its spec id (README 4).

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()`, `on_startup()` (the worker) and `on_event()` (the event relay). `on_event()` makes the feature
the event hub of the installation (ADR-0006): it routes every event on to the runtimes of the subscribing modules
and runs the engine on it. The HTTP API is `features.process_orchestration.router.router`.
"""
from __future__ import annotations

from features.process_orchestration.models.errors import MODULE
from features.process_orchestration.services import engine, event_hub, worker
from portal_common import database

NAME = "process_orchestration"

__all__ = ["MODULE", "NAME", "on_event", "on_startup", "reset"]


def reset() -> None:
    """Empty tables (`database.reset_tables`, through the engine's repository) and a new engine."""
    engine.reset()


def on_startup() -> None:
    database.create_tables(MODULE)
    worker.start_worker()


def on_event(event: dict) -> None:
    """Every CloudEvent of the installation (published here or received through the event inbox): routed on to
    the runtimes of the subscribing modules (event hub, ADR-0006), then starts, continues or ends processes
    (README 6.5). Routing comes first and only enqueues; the engine runs even if routing fails."""
    try:
        event_hub.route(event)
    finally:
        engine.on_event(event)

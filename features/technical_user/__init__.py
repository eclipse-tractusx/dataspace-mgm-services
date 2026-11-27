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
"""Technical User (spec C2-M3): technical users (service accounts) of a company and of its subscriptions.

A company creates its own technical users; Process Orchestration creates and removes the accounts of an
offer subscription and of a wallet; the OSP sees all of them.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `on_startup()`, `reset()` and `on_event()`. The HTTP API is `features.technical_user.router.router`.
"""
from __future__ import annotations

from features.technical_user import services
from features.technical_user.models.errors import MODULE
from portal_common import database

NAME = "technical_user"

__all__ = ["MODULE", "NAME", "on_event", "on_startup", "reset"]


def on_startup() -> None:
    """Creates the tables of the feature's own database (F17) that do not exist yet."""
    database.create_tables(MODULE)


def reset() -> None:
    """Empty state: empty tables and a fresh IAM stand-in."""
    services.reset()


def on_event(event: dict) -> None:
    """Replays the wallet flows when `PROCESS_STUB=true` (README 11.3); every other event is ignored."""
    services.handle_event(event)

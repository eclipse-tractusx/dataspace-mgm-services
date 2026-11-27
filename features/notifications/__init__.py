#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
"""Notifications (spec C11-M1): the inbox of a person, filled by the events of the other modules.

Every event of the relay passes the fixed rules R1 to R17; a rule creates information or a task for the
applicant, for the staff with a permission or for people with a role in a company. A closing event sets a
task done. A person lists, reads, marks and hides the notifications of the own inbox and follows them as
a stream.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()` and `on_event()`. The HTTP API is `features.notifications.router.router`. The work is in
`services/` (`rules`, `engine`, `closing`, `recipients`, `inbox`, `listing`, `marks`) and `managers/`
(`store`, the background `worker` and its `retry` policy, the neighbour client and the stand-in data).
`on_startup()` creates the tables; the delivery thread of `worker` starts on the first job.
"""
from __future__ import annotations

from features.notifications.managers import store, worker
from features.notifications.models import MODULE
from features.notifications.services import closing, engine

NAME = "notifications"

__all__ = ["MODULE", "NAME", "on_event", "on_startup", "reset"]


def on_startup() -> None:
    """Create the tables of the feature's database (`models/tables.py`)."""
    store.create_tables()


def reset() -> None:
    """Fresh state for tests and `/scaffold/reset`. The worker stops first, so a job that is still
    running cannot write into the cleared inbox."""
    worker.reset()
    store.reset()
    closing.reset()


def on_event(event: dict) -> None:
    """Subscriber of the event relay (FRAMEWORK 6); C11-M1 runs before C12-M1 (scaffold registry)."""
    engine.handle(event)

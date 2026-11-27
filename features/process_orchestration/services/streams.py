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
"""Live state for the UI (README 7.6 to 7.8): who sees which stream event, and the current state a new
connection starts with. A controller opens the stream with `portal_common.sse.response()` and the parts of a
`Stream`."""
from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from features.process_orchestration.managers import stream
from features.process_orchestration.models.errors import problem
from features.process_orchestration.services import engine, queries
from features.process_orchestration.services.projections import process_changed, stream_meta
from portal_common.sse import Broker, Message

Visible = Callable[[dict], bool]


@dataclass(frozen=True, slots=True)
class Stream:
    broker: Broker
    visible: Visible                       # whether a stream event (by its meta) belongs to this stream
    initial: Callable[[], list[Message]]   # the current state for a connection without `Last-Event-ID`


def _changed(proc: dict) -> Message:
    return "process-changed", process_changed(proc).model_dump(mode="json")


def of_process(process_id: str) -> Stream:
    """README 7.7: OSP staff follow one process; 404 for an unknown process."""
    queries.process_dict(process_id)

    def current() -> list[Message]:
        e = engine.get_engine()
        with e.lock:
            proc = e.store.get(process_id)   # gone after a reset of the installation
            return [_changed(proc)] if proc else []

    return Stream(stream.BROKER, lambda meta: meta["processId"] == process_id, current)


def of_application(application_id: str, sub: str) -> Stream:
    """README 7.8: the applicant follows the processes of their own application; another person's
    application gives an empty stream, never a 404."""
    try:
        uuid.UUID(application_id)
    except ValueError:
        raise problem(400, "validation", detail="applicationId") from None

    def visible(meta: dict) -> bool:
        return (meta["subjectType"] == "APPLICATION" and meta["subjectId"] == application_id
                and meta["applicantSub"] == sub)

    def current() -> list[Message]:
        e = engine.get_engine()
        with e.lock:
            procs = sorted(e.store.all(), key=lambda p: p["createdAt"])
            return [_changed(p) for p in procs if visible(stream_meta(p))]

    return Stream(stream.BROKER, visible, current)

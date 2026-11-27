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
"""The live processes of one engine on top of the tables (`process_repository`).

The engine changes a process in place, step by step, under its lock, and the API and the tests keep references to
the same objects; so the store holds the live object of every process it started (an identity map, as an ORM
session does) and writes each change through to the tables. Lookups by key go to the indexed columns.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable

from features.process_orchestration.managers import process_repository as repository


class ProcessStore:
    def __init__(self) -> None:
        repository.create_tables()
        self.id = uuid.uuid4().hex                      # scopes the delivered event ids to this engine
        self.processes: dict[str, dict] = {}            # id -> live process, in the order they started
        self.call_log: list[tuple[str, dict]] = []      # (step, input) of every call, for tests and tracing
        self._sequence: dict[str, int] = {}
        self._streamed: dict[str, tuple] = {}           # processId -> last state sent to the UI (README 7.6)

    def first_delivery(self, event_id: str | None) -> bool:
        """README 6.7: an event `id` is processed once; an event without `id` always counts."""
        return repository.record_event(self.id, event_id) if event_id else True

    def add(self, proc: dict) -> dict:
        self.processes[proc["id"]] = proc
        self._sequence[proc["id"]] = len(self._sequence)
        self.save(proc)
        return proc

    def save(self, proc: dict) -> None:
        repository.save(proc, self._sequence[proc["id"]])

    def get(self, process_id: str) -> dict | None:
        return self.processes.get(process_id)

    def all(self) -> list[dict]:
        return list(self.processes.values())

    def _live(self, ids: Iterable[str]) -> list[dict]:
        return [self.processes[pid] for pid in ids if pid in self.processes]

    def open_process(self, flow_key: str, value: object, open_states: Iterable[str]) -> dict | None:
        """The open process of a flow with this correlation value (README 6.5)."""
        return next((p for p in self._live(repository.ids_of_correlation(flow_key, value))
                     if p["status"] in open_states), None)

    def of_subject(self, subject_type: str, subject_id: str) -> list[dict]:
        return self._live(repository.ids_of_subject(subject_type, subject_id))

    def record_call(self, call: str, data: dict) -> None:
        self.call_log.append((call, data))

    def record_retrigger(self, entry: dict) -> None:
        repository.add_audit(entry)

    def stream_changed(self, process_id: str, state: tuple) -> bool:
        """Remembers the state sent to the UI; False when it is the one sent last."""
        if self._streamed.get(process_id) == state:
            return False
        self._streamed[process_id] = state
        return True

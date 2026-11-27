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
"""Outbound delivery of events to other runtimes (FRAMEWORK 6, ADR-0002, ADR-0006).

Inside a process the relay delivers events in memory. When modules run as separate pods, the events a
module publishes must also reach the others. Process Orchestration (C12-M1) is the event hub of a split
installation (ADR-0006): every locally published CloudEvent is posted to the event inbox
`<address of C12-M1>/api/v1/events/inbox`, the address from the neighbour rule of FRAMEWORK 4.7
(`C12_M1_URL`, `MODULE_URLS`; nothing when C12-M1 runs in this process or is a stand-in). The hub feeds its
engine and dispatches the event on to the runtimes of the subscribing modules (`dispatch`). `EVENT_SINKS`
(comma separated base addresses, e.g. `http://c3-m1:8000`) still adds further inboxes, as before
(ADR-0002). Deliveries use the CloudEvents HTTP binding, structured mode, with the service token of the
publishing module (`svc-<module>`), so the receiving inbox checks the event like one from its publisher.

- Off the request path: `submit` and `dispatch` only enqueue; worker threads deliver, so a slow peer never
  slows a request.
- At least once: retries with exponential backoff; the inbox deduplicates by `source` and `id`.
- Bounded: a full queue drops the oldest event and counts it in `dropped` (a broker with a durable outbox
  is the next step, see ADR-0002).
- No loops: events received through the inbox are never submitted again; only the hub dispatches them on,
  never to its own address, and an event that comes back to a runtime that knows it is delivered once.
- Connection pooling: one keep-alive `httpx.Client` for all deliveries.
"""
from __future__ import annotations

import collections
import logging
import os
import threading
import time

import httpx

from . import settings, tokens

log = logging.getLogger("portal.events.forwarder")
INBOX_PATH = "/api/v1/events/inbox"
STRUCTURED = "application/cloudevents+json"
RETRY_DELAYS = (0.2, 0.5, 1.0, 2.0, 5.0)   # seconds before attempt 2..6
QUEUE_MAX = 10_000
WORKERS = 2
HUB = "c12-m1"   # Process Orchestration, the event hub of a split installation (ADR-0006)


def sinks() -> list[str]:
    return [s.strip().rstrip("/") for s in os.environ.get("EVENT_SINKS", "").split(",") if s.strip()]


def hub() -> str:
    """Address of the event hub's runtime, empty when the hub runs in this process or is a stand-in."""
    from . import neighbours  # neighbours -> standin -> layout: imported late, events imports this module

    if neighbours.in_process(HUB) or neighbours.is_standin(HUB):
        return ""
    return neighbours.address(HUB)


def targets() -> list[str]:
    """Inboxes of a locally published event: the hub, then `EVENT_SINKS`; never this runtime itself."""
    return _distinct([hub(), *sinks()])


def _distinct(addresses: list[str]) -> list[str]:
    own = settings.base_url()
    out: list[str] = []
    for a in (a.rstrip("/") for a in addresses):
        if a and a != own and a not in out:
            out.append(a)
    return out


class Forwarder:
    def __init__(self) -> None:
        self._queue: collections.deque[tuple[dict, list[str]]] = collections.deque()
        self._cv = threading.Condition()
        self._threads: list[threading.Thread] = []
        self._stop = False
        self._client: httpx.Client | None = None
        self._pending = 0
        self.dropped = 0
        self.failures: list[dict] = []

    def submit(self, event: dict) -> None:
        """A locally published event: to the hub and to `EVENT_SINKS` (`targets()`); nothing in a monolith."""
        self.dispatch(event, targets())

    def dispatch(self, event: dict, addresses: list[str]) -> None:
        """Delivers `event` to the inboxes of `addresses` (base addresses of runtimes); the hub routes with it."""
        addresses = _distinct(addresses)
        if not addresses:
            return
        with self._cv:
            if len(self._queue) >= QUEUE_MAX:
                self._queue.popleft()
                self.dropped += 1
                self._pending -= 1
            self._queue.append((event, addresses))
            self._pending += 1
            self._cv.notify()
        self._ensure_started()

    def _ensure_started(self) -> None:
        with self._cv:
            if self._threads and all(t.is_alive() for t in self._threads):
                return
            self._stop = False
            if self._client is None:
                self._client = httpx.Client(timeout=5.0, limits=httpx.Limits(max_keepalive_connections=20))
            self._threads = [threading.Thread(target=self._loop, name=f"event-forwarder-{i}", daemon=True)
                             for i in range(WORKERS)]
            for t in self._threads:
                t.start()

    def _loop(self) -> None:
        while True:
            with self._cv:
                while not self._queue and not self._stop:
                    self._cv.wait()
                if self._stop and not self._queue:
                    return
                event, addresses = self._queue.popleft()
            try:
                self._send_all(event, addresses)
            finally:
                with self._cv:
                    self._pending -= 1
                    self._cv.notify_all()

    def _send_all(self, event: dict, addresses: list[str]) -> None:
        module = event["source"].removeprefix("urn:")
        for sink in addresses:
            self._send(sink, module, event)

    def _send(self, sink: str, module: str, event: dict) -> None:
        error = ""
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                r = self._client.post(sink + INBOX_PATH, json=event, headers={
                    "Content-Type": STRUCTURED, "Authorization": "Bearer " + tokens.service_token(module)})
                if r.status_code == 202:
                    return
                error = f"HTTP {r.status_code}"
                if 400 <= r.status_code < 500 and r.status_code not in (401, 408, 429):
                    break   # the peer rejects the event itself; a retry cannot help
            except Exception as exc:  # noqa: BLE001 - network or token errors are retried
                error = repr(exc)
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
        self.failures.append({"sink": sink, "id": event["id"], "type": event["type"], "error": error})
        log.error("event %s %s not delivered to %s: %s", event["type"], event["id"], sink, error)

    def wait_idle(self, timeout: float = 10.0) -> bool:
        with self._cv:
            return self._cv.wait_for(lambda: self._pending <= 0, timeout)

    def stop(self) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify_all()

    def reset(self) -> None:
        with self._cv:
            self._pending -= len(self._queue)
            self._queue.clear()
            self.failures.clear()
            self.dropped = 0


FORWARDER = Forwarder()

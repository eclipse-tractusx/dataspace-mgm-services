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
"""Built-in stand-in of the issuer, route `STUB` (README 11.6).

It remembers the order and, after `STUB_ISSUER_DELAY_SECONDS`, calls the processing of the status report
(README 7.4) in the same process, like an issuer calling back over HTTP would.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from features.credentials.managers import config
from features.credentials.managers.credential_store import store
from features.credentials.models.values import STUB
from portal_common.problems import Problem

log = logging.getLogger("c4-m1.routes")


@dataclass(eq=False)
class _Pending:
    """An order whose report is still to come; `generation` ties it to the state before a reset."""

    order: dict
    generation: int
    fired: bool = False
    timer: threading.Timer | None = field(default=None, repr=False)


class StubRoute:
    """Remembers the orders and reports their outcome after the configured delay."""

    name: str = STUB

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.orders: list[dict] = []
        self._pending: list[_Pending] = []
        self._timers: list[threading.Timer] = []   # every started timer, so that flush() can wait for them
        self._generation = 0

    def prepare(self, ctx: dict) -> None:
        """No holder access, no holder registration for the stand-in."""

    def order(self, ctx: dict, credential_type: str, attempt: int) -> tuple[str, str | None]:
        order = {"company_id": ctx["company"]["id"], "credential_type": credential_type,
                 "bpn": ctx["company"]["bpn"].upper(), "attempt": attempt}
        delay = config.stub_issuer_delay()
        with self._lock:
            self.orders.append(order)
            entry = _Pending(order, self._generation)
            timer = entry.timer = threading.Timer(delay, self._fire, args=(entry,))
            timer.daemon = True
            self._pending.append(entry)
            self._timers.append(timer)
            timer.start()
        return f"stub-{attempt}", None

    def _fire(self, entry: _Pending) -> None:
        from features.credentials.services import credential_service
        with self._lock:
            if entry.fired or entry.generation != self._generation:
                return
            entry.fired = True
            if entry in self._pending:
                self._pending.remove(entry)
        order = entry.order
        failing = order["credential_type"] in config.stub_issuer_fail_types()
        try:
            # Wait for a step that is still ordering this company: with a delay of 0 the timer fires before the
            # row of the order is stored, and the report would find no order (README 6.9 per-company lock).
            with store().transaction(order["company_id"]):
                credential_service.report_status(order["credential_type"].lower(), order["bpn"],
                                                 "UNSUCCESSFUL" if failing else "SUCCESSFUL",
                                                 "Issuance declined by the stand-in" if failing else None)
        except Problem as e:   # for example the row is gone after a reset
            log.warning("stand-in report for %s/%s not processed: %s", order["bpn"], order["credential_type"], e)

    def flush(self) -> None:
        """Fires every pending timer at once, in order of the orders, and waits for timers that already
        fired in their own thread (tests)."""
        while True:
            with self._lock:
                entry = next((e for e in self._pending if not e.fired), None)
            if entry is None:
                break
            if entry.timer:
                entry.timer.cancel()
            self._fire(entry)
        with self._lock:
            started = list(self._timers)
        for timer in started:
            timer.join(5)

    def cancel(self, row: dict) -> None:
        """An open order is cancelled: nothing to do at the stand-in (a late report revokes at once)."""

    def revoke(self, row: dict) -> bool:
        return True                                                          # README 11.6: always successful

    def reset(self) -> None:
        with self._lock:
            self._generation += 1
            for e in self._pending:
                if e.timer:
                    e.timer.cancel()
            self._pending.clear()
            self._timers.clear()
            self.orders.clear()

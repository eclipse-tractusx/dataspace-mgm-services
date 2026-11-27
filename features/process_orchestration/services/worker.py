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
"""Background worker for due repetitions and await deadlines (README 4), every `WORKER_POLL_SECONDS`."""
from __future__ import annotations

import logging
import threading

from features.process_orchestration.managers import config
from features.process_orchestration.models.errors import MODULE
from features.process_orchestration.services import engine

log = logging.getLogger(MODULE)
_worker: threading.Thread | None = None
_stop = threading.Event()


def start_worker() -> None:
    global _worker
    if _worker and _worker.is_alive():
        return
    _stop.clear()
    interval = config.worker_poll_seconds()

    def loop() -> None:
        while not _stop.wait(interval):
            try:
                engine.get_engine().tick()
            except Exception:  # noqa: BLE001 - the worker must keep running
                log.exception("worker tick failed")

    _worker = threading.Thread(target=loop, name="c12-worker", daemon=True)
    _worker.start()


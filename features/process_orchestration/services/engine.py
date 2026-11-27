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
"""C12-M1 Process Orchestration: runs the flows of `flows.yaml` (README sections 4 to 6, 11).

Flow execution: events start, correlate and end processes, steps run one after the other, with
repetitions, waits for events and retriggers. The flow catalogue, the process store and the calls
to the other modules are managers (`managers/`); the dispatch of a step to its module is
`services.dispatch`. A step `<module>.<step>` of flows.yaml is called in-process through the
module's interface (`<interface>.<step in snake_case>(input)`, `portal_common.layout`) and a lookup
`<module>.<operationId>` as `<operationId in snake_case>(**params)` (README 4); a module with an HTTP
address is called over HTTP with the service token of `svc-c12-m1`. With an empty module address the
built-in stand-in answers (README 11.3): steps `DONE` at once with the stand-in results, lookups with
the answers of section 14 (`STANDIN_FILE` replaces both). Lookups follow README 6.8: `query` =
`<module>.<operationId>`, field paths, object mappings and `join`; a failed lookup is an error of the
step, never `found: false`. In memory: a restart loses the processes (upgrade: tables of README 5).

Events are CloudEvents (FRAMEWORK 6): the name is `type`, a repeated delivery has the same `id`
(README 6.7), and the field names of a flow (`trigger.when`, `subject.key`, `correlateBy`, process
variables, the payload of `completesOn`) are fields of `data`. The events of C12-M1 have the
`source` `urn:c12-m1`.
"""
from __future__ import annotations

import copy
import datetime as dt
import re
import threading
import uuid
from pathlib import Path

from features.process_orchestration.managers import config, flow_catalogue, process_repository, standin_data, stream
from features.process_orchestration.managers.flow_catalogue import completion_types, known_events  # noqa: F401 (API)
from features.process_orchestration.managers.process_store import ProcessStore
from features.process_orchestration.models.errors import MODULE, FlowError, LookupFailed  # noqa: F401 (API)
from features.process_orchestration.models.states import FINAL_STEP, OPEN
from features.process_orchestration.services import dispatch, sources
from features.process_orchestration.services.projections import iso, process_changed, stream_meta
from portal_common import events


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _data(event: dict) -> dict:
    """Content of a CloudEvent (FRAMEWORK 6): the JSON object in `data`."""
    data = event.get("data")
    return dict(data) if isinstance(data, dict) else {}


class Engine:
    def __init__(self, flows_file: str | Path | None = None):
        self.doc, self.warnings = flow_catalogue.load(flows_file)
        self.flows = {fl["key"]: fl for fl in self.doc["flows"]}
        self.version = self.doc.get("version", 1)
        self.defaults = self.doc.get("defaults") or {}
        self.lookups = self.doc.get("lookups") or {}
        self.clock = _now
        self.lock = threading.RLock()
        self.retry_base = config.retry_base()
        self.retry_factor = config.retry_factor()
        self.retry_max = config.retry_max()
        self.max_attempts = config.max_attempts(self.defaults.get("maxAttempts", 5))
        self.timeout = config.step_timeout()
        self.standin = standin_data.load()
        self.store = ProcessStore()

    # the state lives in the process store (managers/process_store.py)
    @property
    def processes(self) -> dict[str, dict]:
        return self.store.processes

    @property
    def call_log(self) -> list[tuple[str, dict]]:
        return self.store.call_log

    # ---------------------------------------------------------------- events (README 6.5)
    def on_event(self, event: dict) -> None:
        """A CloudEvent of the relay (FRAMEWORK 6): `type` is the name, the fields are in `data`;
        an `id` is processed once (README 6.7)."""
        with self.lock:
            eid, etype, data = event.get("id"), event.get("type"), _data(event)
            if not self.store.first_delivery(eid):
                return
            touched = []
            for fl in self.flows.values():
                corr = fl["correlateBy"]
                proc = self.store.open_process(fl["key"], data.get(corr), OPEN) if corr in data else None
                if proc and etype in self._named_events(fl):
                    proc["variables"].update(data)
                    proc["inbox"].append({"type": etype, "payload": dict(data), "used": False})
                    if etype in (fl.get("endOn") or []) and self._decision_open(proc):
                        self._end(proc, etype)   # README 6.5 point 5: only before every waitFor event arrived
                    touched.append(proc)
                elif etype == fl["trigger"]["event"] and not proc and self._trigger_matches(fl, data):
                    touched.append(self._start(fl, eid, data))
            for proc in touched:
                self.advance(proc)
                self._changed(proc)

    @staticmethod
    def _decision_open(proc: dict) -> bool:
        waits = {st["waitFor"] for st in proc["flow"]["steps"] if st.get("waitFor")}
        arrived = {e["type"] for e in proc["inbox"]}
        return not waits or not waits <= arrived

    @staticmethod
    def _named_events(fl: dict) -> set[str]:
        names = set(fl.get("endOn") or [])
        for st in fl["steps"]:
            if st.get("waitFor"):
                names.add(st["waitFor"])
            names |= completion_types(st) | set(st.get("failsOn") or [])
        return names

    @staticmethod
    def _trigger_matches(fl: dict, data: dict) -> bool:
        """README 6.5 point 1: the fields of `trigger.when` are fields of the event's `data`."""
        return all(data.get(k) == v for k, v in (fl["trigger"].get("when") or {}).items())

    def _start(self, fl: dict, event_id: str | None, data: dict) -> dict:
        now = self.clock()
        proc = {
            "id": str(uuid.uuid4()), "flowKey": fl["key"], "flowVersion": self.version,
            "flow": copy.deepcopy(fl),  # README 4: a process keeps the flow version it started with
            "subjectType": fl["subject"]["type"], "subjectId": data.get(fl["subject"]["key"]),
            "correlationKey": fl["correlateBy"], "correlationValue": data.get(fl["correlateBy"]),
            "status": "RUNNING", "variables": dict(data), "lookups": {}, "inbox": [],
            "triggerEventId": event_id, "endReason": None,
            "createdAt": now, "updatedAt": now, "finishedAt": None,
            "steps": [{"stepRunId": str(uuid.uuid4()), "stepKey": st["key"], "call": st["call"], "state": "WAITING",
                       "attempts": 0, "maxAttempts": st.get("maxAttempts", self.max_attempts), "nextAttemptAt": None,
                       "awaitUntil": None, "result": None, "lastError": None, "startedAt": None, "finishedAt": None,
                       "attemptHistory": []} for st in fl["steps"]],
        }
        self.store.add(proc)
        self._publish("ProcessStarted", proc)
        return proc

    def _publish(self, etype: str, proc: dict, **extra: object) -> None:
        """Events of C12-M1 (README 10) as CloudEvents with `source` `urn:c12-m1` (FRAMEWORK 6)."""
        data = {"processId": proc["id"]}
        if etype != "ProcessStepRetriggered":
            data |= {"flowKey": proc["flowKey"], "subjectType": proc["subjectType"], "subjectId": proc["subjectId"]}
        events.publish(MODULE, etype, data | extra)

    def _end(self, proc: dict, reason: str) -> None:
        for sr in proc["steps"]:
            if sr["state"] in ("WAITING", "READY", "AWAITING_EVENT"):
                sr["state"] = "SKIPPED"
        proc["status"], proc["endReason"] = "ENDED", reason
        proc["finishedAt"] = proc["updatedAt"] = self.clock()
        self._changed(proc)
        self._publish("ProcessEnded", proc)

    # ---------------------------------------------------------------- progress (README 6.3, 6.4)
    def advance(self, proc: dict) -> None:
        """Runs the steps in order until one has to wait; then sets the status of the process."""
        with self.lock:
            if proc["status"] in ("ENDED", "COMPLETED"):
                return
            for st, sr in zip(proc["flow"]["steps"], proc["steps"], strict=True):
                stop = self._advance_step(proc, st, sr)
                if stop is not None:
                    if stop:
                        self._set_status(proc, stop)
                    return
            proc["status"] = "COMPLETED"
            proc["finishedAt"] = proc["updatedAt"] = self.clock()
            self._changed(proc)
            self._publish("ProcessCompleted", proc)

    def _advance_step(self, proc: dict, st: dict, sr: dict) -> str | None:
        """One step: None when it is finished (go on with the next), otherwise the status the process gets now
        (`""`: the process ended during the call and keeps its status)."""
        if sr["state"] in FINAL_STEP:
            return None
        blocked = self._blocked(proc, st, sr)
        if blocked:
            return blocked
        if sr["state"] == "READY":
            stop = self._run_ready(proc, st, sr)
            if stop is not None:
                return stop
        if sr["state"] == "AWAITING_EVENT":
            self._check_completion(proc, st, sr)
        if sr["state"] in FINAL_STEP:
            return None
        return "FAILED" if sr["state"] == "FAILED" else "RUNNING"

    def _blocked(self, proc: dict, st: dict, sr: dict) -> str | None:
        """The status of a process whose step cannot run now; a `WAITING` step whose event is there becomes READY."""
        if sr["state"] == "FAILED":
            return "FAILED"
        if sr["nextAttemptAt"] and sr["nextAttemptAt"] > self.clock():
            return "RUNNING"      # due later; the worker picks it up
        if sr["state"] == "WAITING":
            if st.get("waitFor") and not any(e["type"] == st["waitFor"] for e in proc["inbox"]):
                return "WAITING"
            sr["state"] = "READY"
        return None

    def _run_ready(self, proc: dict, st: dict, sr: dict) -> str | None:
        """README 6.8: the lookups run when the step is READY, before its `when`; then the call (README 6.3)."""
        try:
            when_ok = self._prepare(proc, st)
        except LookupFailed as e:
            self._error(proc, sr, e.error)
            return "FAILED" if sr["state"] == "FAILED" else "RUNNING"
        if not when_ok:
            sr["state"], sr["finishedAt"] = "SKIPPED", self.clock()
            return None
        proc["status"] = "RUNNING"   # README 6.4: a step is IN_PROGRESS (shown in the stream, 7.6)
        self._call(proc, st, sr)
        if proc["status"] == "ENDED":   # endOn during the call (README 6.3)
            if sr["state"] not in FINAL_STEP:
                sr["state"] = "SKIPPED"
            return ""
        return None

    def _set_status(self, proc: dict, status: str) -> None:
        proc["status"], proc["updatedAt"] = status, self.clock()
        self._changed(proc)

    def _changed(self, proc: dict) -> None:
        """Stores the process (every operation ends here for each process it touched), then README 7.6:
        `process-changed` after every stored change of the process status or of a step state; states passed
        within one call are combined. `meta` decides who sees it."""
        self.store.save(proc)
        changed = process_changed(proc)
        state = (changed.status, changed.end_reason, tuple((s.step_key, s.state) for s in changed.steps))
        if self.store.stream_changed(proc["id"], state):
            stream.BROKER.publish("process-changed", changed.model_dump(mode="json"), stream_meta(proc))

    def _take_event(self, proc: dict, types: set[str]) -> dict | None:
        for e in proc["inbox"]:
            if e["type"] in types and not e["used"]:
                e["used"] = True
                return e
        return None

    # ---------------------------------------------------------------- sources and lookups
    def _prepare(self, proc: dict, st: dict) -> bool:
        """Runs the lookups the step needs; returns whether `when` is met."""
        names = [st["lookup"]] if st.get("lookup") else []
        names += [src.split(".")[1] for src in (st.get("when") or {}) if src.startswith("lookup.")]
        for name in names:
            if name not in proc["lookups"]:
                proc["lookups"][name] = dispatch.run_lookup(proc, name, self.lookups[name], self.standin, self.timeout)
        return all(sources.resolve(proc, src) == want for src, want in (st.get("when") or {}).items())

    # ---------------------------------------------------------------- calling a step
    def _call(self, proc: dict, st: dict, sr: dict, trigger: str = "WORKER", by: str | None = None) -> None:
        now = self.clock()
        sr["state"], sr["attempts"] = "IN_PROGRESS", sr["attempts"] + 1
        sr["startedAt"] = sr["startedAt"] or now
        attempt = {"number": sr["attempts"], "trigger": trigger, "triggeredBy": by, "startedAt": iso(now),
                   "finishedAt": None, "outcome": None, "errorType": None}
        sr["attemptHistory"].append(attempt)
        data = sources.build_input(proc, st, sr)
        self.store.record_call(st["call"], data)
        outcome = dispatch.invoke(proc, st, data, self.standin, self.timeout)
        attempt["finishedAt"] = iso(self.clock())
        if "error" in outcome:
            attempt["outcome"], attempt["errorType"] = "ERROR", outcome["error"].get("type")
            sr["attempts"] -= 1   # _error counts the attempt
            return self._error(proc, sr, outcome["error"])
        state = outcome.get("state")
        attempt["outcome"], sr["nextAttemptAt"] = state, None
        if state == "RUNNING":
            sr["state"], sr["awaitUntil"] = "AWAITING_EVENT", self.clock() + self._await_timeout(st)
        else:
            sr["state"], sr["finishedAt"], sr["result"] = "DONE", self.clock(), outcome.get("result") or {}
            self._take_event(proc, completion_types(st))   # a module may also publish the event
        self._changed(proc)

    def _error(self, proc: dict, sr: dict, err: dict) -> None:
        sr["attempts"] += 1
        sr["lastError"] = err
        if err.get("retryable") is True and sr["attempts"] < sr["maxAttempts"]:
            wait = min(self.retry_base * self.retry_factor ** (sr["attempts"] - 1), self.retry_max)
            sr["state"] = "READY" if sr["state"] == "IN_PROGRESS" else sr["state"]
            sr["nextAttemptAt"] = self.clock() + dt.timedelta(seconds=wait)
        else:
            self._fail(proc, sr, err.get("type"), bool(err.get("retryable")))

    def _await_timeout(self, st: dict) -> dt.timedelta:
        # step setting > AWAIT_TIMEOUT > defaults of the flow file
        duration = st.get("awaitTimeout") or config.await_timeout() or self.defaults.get("awaitTimeout") or "PT24H"
        m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration)
        if m is None:
            raise FlowError(f"awaitTimeout {duration}: not an ISO 8601 duration of days, hours, minutes, seconds")
        d, h, mi, s = (int(x or 0) for x in m.groups())
        return dt.timedelta(days=d, hours=h, minutes=mi, seconds=s)

    def _check_completion(self, proc: dict, st: dict, sr: dict) -> None:
        ev = self._take_event(proc, completion_types(st) | set(st.get("failsOn") or []))
        if ev and ev["type"] in (st.get("failsOn") or []):
            sr["lastError"] = {"type": f"event:{ev['type']}", "status": None, "title": ev["payload"].get("reason"),
                               "retryable": False}
            return self._fail(proc, sr, f"event:{ev['type']}", False)
        if ev:
            sr["state"], sr["finishedAt"], sr["result"] = "DONE", self.clock(), ev["payload"]
            for c in st.get("completesOn") or []:
                if isinstance(c, dict) and c["event"] == ev["type"]:
                    proc["variables"].update(c.get("set") or {})
            return
        if sr["awaitUntil"] and self.clock() > sr["awaitUntil"]:
            sr["lastError"] = {"type": "await-timeout", "status": None, "title": "no completing event",
                               "retryable": False}
            self._fail(proc, sr, "await-timeout", False)

    def _fail(self, proc: dict, sr: dict, error_type: str | None, retryable: bool) -> None:
        sr["state"], sr["finishedAt"], sr["nextAttemptAt"] = "FAILED", self.clock(), None
        self._set_status(proc, "FAILED")
        self._publish("ProcessStepFailed", proc, stepKey=sr["stepKey"], errorType=error_type, retryable=retryable)

    # ---------------------------------------------------------------- worker and retrigger
    def tick(self) -> None:
        """Worker run (README 4): due repetitions and passed await deadlines."""
        with self.lock:
            for proc in self.store.all():
                if proc["status"] == "RUNNING":
                    self.advance(proc)
                    self._changed(proc)

    def retrigger(self, proc: dict, step_key: str, sub: str, comment: str | None = None) -> dict | None:
        with self.lock:
            sr = next(r for r in proc["steps"] if r["stepKey"] == step_key)
            if sr["state"] != "FAILED":
                return None
            sr.update(state="READY", attempts=0, nextAttemptAt=None,
                      awaitUntil=None, finishedAt=None)
            proc["status"] = "RUNNING"
            self.store.record_retrigger({"at": iso(self.clock()), "sub": sub, "processId": proc["id"],
                                         "stepKey": step_key, "comment": comment})
            self._publish("ProcessStepRetriggered", proc, stepKey=step_key, retriggeredBy=sub)
            result = dict(sr)
            self.advance(proc)
            self._changed(proc)
            return result


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine


def reset() -> Engine:
    """Empty state: no stream events, empty tables and a new engine."""
    global _engine
    stream.reset()
    process_repository.reset()
    _engine = Engine()
    return _engine


def on_event(event: dict) -> None:
    get_engine().on_event(event)

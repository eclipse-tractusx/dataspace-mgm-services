<!--
 Copyright (c) 2026 Catena-X Automotive Network e.V.
 Copyright (c) 2026 Contributors to the Eclipse Foundation

 See the NOTICE file(s) distributed with this work for additional
 information regarding copyright ownership.

 This program and the accompanying materials are made available under the
 terms of the Apache License, Version 2.0 which is available at
 https://www.apache.org/licenses/LICENSE-2.0.

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

 AI Disclosure: This file was entirely AI-generated.
 The AI-generated portions are made available under CC0-1.0 and not subject
 to the project's license. The human contributor has reviewed and verified
 that the content is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# Process Orchestration (C12-M1)

Migrated from `modules/c12_m1/` (spec `spec/C12-M1-ProcessOrchestration`).

## What it does

Process Orchestration runs the flows of an installation. A flow is data in `flows.yaml`: a trigger event, a list
of steps of other modules and the events that complete them. When a trigger event arrives (for example
`ApplicationSubmitted`), the feature starts a process, calls the steps of the other modules in the order of the
flow, waits for decisions and for the completing events of long-running steps, repeats steps after temporary
errors and marks a step `FAILED` when it fails for good. The other modules do not know Process Orchestration; they
offer steps under `/steps/...` and publish events.

Process Orchestration is also the **event hub** of a split installation
([ADR-0006](../../docs/architecture/decisions/ADR-0006-process-orchestration-as-event-hub.md)): every runtime
forwards the CloudEvents it publishes to the event inbox of the runtime of this feature, and the feature routes each
event on to the runtimes of the other subscribing features before it runs its flows. In the monolith every
subscriber is in-process and nothing leaves the process.

Callers: the event relay of the installation (every published CloudEvent, and the events of the other runtimes
through the event inbox `POST /api/v1/events/inbox` of the base skeleton), OSP staff in the UI (view processes, retrigger a failed step, follow a process live), applicants
in the UI (follow the processes of their own application live), other modules (Subscriptions asks for the
processes of a subscription) and Notifications (reacts to `ProcessStepFailed`).

## How it works

**Flows and states.** At start-up the flow catalogue is loaded and checked against the spec (README 6.2): every
step, lookup and event must exist in the openapi.yaml or README of its module; otherwise the engine does not start.
An event starts a process of every flow whose trigger it matches and that has no open process for the same
correlation value; an event that a running process names (`waitFor`, `completesOn`, `failsOn`, `endOn`) goes to
that process's inbox. Steps run one after the other: `WAITING` -> `READY` -> `IN_PROGRESS` -> `DONE`, or
`AWAITING_EVENT` until the completing event arrives (at most `AWAIT_TIMEOUT`), `SKIPPED` when `when` does not hold,
`FAILED` after the last attempt. A process is `RUNNING`, `WAITING` (for a decision), `FAILED`, `COMPLETED` or
`ENDED` (an `endOn` event before the decision). A step `<module>.<step>` and a lookup `<module>.<operationId>` name
the module by spec id; the address comes from `portal_common.neighbours` (`<MODULE>_URL`, `MODULE_URLS`):
in-process through the module's interface (`portal_common.layout`, whether the module still lives in `modules/`
or is a feature), over HTTP with the service token of `svc-c12-m1`, or the built-in stand-in for an empty address
(README 11.3).

**Folder map.**

| Folder | Contents |
|---|---|
| `controllers/processes/` | `GET /processes`, `GET /processes/{processId}` |
| `controllers/processes/steps/` | `GET /processes/{processId}/steps/{stepKey}`, `POST .../retrigger` |
| `controllers/processes/events/` | `GET /processes/{processId}/events` (Server-Sent Events for OSP staff) |
| `controllers/applications/events/` | `GET /applications/{applicationId}/events` (Server-Sent Events for the applicant) |
| `controllers/flows/` | `GET /flows`, `GET /flows/{flowKey}` |
| `controllers/internal/processes/` | `GET /internal/processes` (query of other modules) |
| `services/engine.py` | flow execution: events, step progress, repetitions, await deadlines, retrigger |
| `services/dispatch.py` | step and lookup dispatch: in-process, HTTP or built-in stand-in |
| `services/sources.py` | input sources, field paths, object mappings and `join` (README 6.1, 6.8) |
| `services/projections.py`, `queries.py`, `streams.py` | the views of the API and of the live stream |
| `services/worker.py` | background worker for due repetitions and await deadlines |
| `services/event_hub.py` | the event hub: the runtimes each event is routed on to (ADR-0006) |
| `managers/event_routes.py` | subscribing features, their addresses and the delivery to their event inbox |
| `managers/flow_catalogue.py` | loads `flows.yaml` and checks it against the spec |
| `managers/process_repository.py`, `process_store.py` | the tables of the processes and the live processes of the engine |
| `managers/neighbour_client.py` | the calls to the other modules, in-process and over HTTP |
| `managers/standin_data.py`, `data/standin.json` | the answers of the built-in stand-in |
| `managers/stream.py` | the broker of the live stream (replay after `Last-Event-ID`) |
| `managers/config.py` | the environment variables below |
| `models/process.py` | pydantic models of the API: `ProcessSummary`, `Page[ProcessSummary]`, `Process`, `StepRun`, `StepRunDetail`, `StepError`, `StepAttempt`, `ProcessChanged`, `RetriggerRequest`, `Flow` |
| `models/states.py` | value sets `SubjectType`, `ProcessStatus`, `StepState` |
| `models/tables.py` | SQLModel tables `process`, `step_run`, `processed_event`, `audit_entry` |
| `models/errors.py` | `MODULE`, `FlowError`, `LookupFailed` |

**Interface.** `interface.py` has the one query of README 9, `find_processes_of_subject(subjectType, subjectId)`.
Process Orchestration has no steps.

**Events.** Consumed: every event of the installation (`on_event`: first routed on by the hub, then given to the
engine). Routing: the hub sends an event to the event inbox of each runtime that serves a subscribing feature
(a feature index with `on_event`, addressed by `<MODULE>_URL` / `MODULE_URLS`), except its own runtime, the
publisher's runtime and stand-ins, with the token of the publishing module's service account, once per runtime;
the relay delivers each `source` and `id` once, so a copy that comes back is not delivered again. Published (source `urn:c12-m1`):
`ProcessStarted`, `ProcessStepFailed`, `ProcessStepRetriggered`, `ProcessCompleted`, `ProcessEnded`. The UI
stream event `process-changed` carries the state of a process (IDs, keys and states only).

**Configuration** (`managers/config.py`, read when the engine is built): `FLOWS_CHECK` (`strict` or `warn`),
`RETRY_BASE_SECONDS`, `RETRY_FACTOR`, `RETRY_MAX_SECONDS`, `MAX_ATTEMPTS`, `STEP_TIMEOUT_SECONDS`, `AWAIT_TIMEOUT`,
`STANDIN_FILE`, `WORKER_POLL_SECONDS`. Shared code reads `FLOWS_FILE` (default: `flows.yaml` of the spec,
`portal_common.spec`) and `SSE_REPLAY_SIZE` (`portal_common.sse`).

**Persistence.** Processes and step runs, the delivered event ids and the retrigger audit are SQLModel tables in
the feature's own database (`PROCESS_ORCHESTRATION_DATABASE_URL`, then `C12_M1_DATABASE_URL`, then `DATABASE_URL`;
without one a private in-memory SQLite database). The engine works on its live process objects under its lock
and writes every change through to the tables; lookups by correlation value and by subject use the indexed
columns. The installation resets every feature when it starts, so processes do not survive a restart yet.

**Run and test it alone.**

    RUNTIME=process_orchestration uv run python -m runtimes
    uv run pytest -q tests/test_c12_m1_*.py

## Links

- Spec: [README](../../spec/C12-M1-ProcessOrchestration/README.md), [openapi.yaml](../../spec/C12-M1-ProcessOrchestration/openapi.yaml), [flows.yaml](../../spec/C12-M1-ProcessOrchestration/flows.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md)
- [ADR-0006](../../docs/architecture/decisions/ADR-0006-process-orchestration-as-event-hub.md) (event hub)

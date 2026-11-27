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

# C12-M1 open questions

The open points of the spec are in [open-points.md](../../spec/C12-M1-ProcessOrchestration/open-points.md); these
are the points of this implementation.

1. **FRAMEWORK 4.1, base path `/api/c12-m1`** "until the common path convention is settled". Implemented: served under the readable feature name `/api/process-orchestration` (ADR-0003, decision 2); `/api/c12-m1` answers 404. Problem types (`urn:c12-m1:problem:...`), event sources (`urn:c12-m1`), permissions (`query_c12_m1`) and the service account `svc-c12-m1` keep the spec id. Steps and lookups of `flows.yaml` keep naming modules by spec id; the engine finds their address through `portal_common.layout` and `neighbours`.
2. **README 5, persistence.** Implemented: processes, delivered event ids and the retrigger audit are kept in memory (`managers/process_store.py`); a restart loses them. The tables of README 5 are not built yet.
3. **README 7.3, attempts of a step run.** openapi.yaml names the list `attemptHistory`; the hackathon module answered `attempts_`, and the migration keeps that wire format (`StepRunDetail` in `models/process.py`). To be aligned with the spec in a follow-up together with the UI.
4. **README 6.7, delivered event ids per engine.** The ids are stored per engine instance (`processed_event.engine_id`), so a new engine (after a reset) processes a redelivered event again, as before the migration.
5. **README 3 and FRAMEWORK 1, the event hub (ADR-0006).** README 3 lists "transport of events (event bus of the installation with an outbox per module)" as not part of C12-M1, FRAMEWORK 1 says the modules do not know Process Orchestration, and open point 4 of the spec (event transport, broker) is still open. Implemented on request of the maintainers: in a split installation the feature is the event hub; every runtime forwards its events to the runtime of C12-M1 (found by the neighbour rule) and `on_event` routes them on to the runtimes with subscribers. The publishing modules do not change and do not know the hub (only the shared forwarder does), and the API, events and flows of C12-M1 do not change. The HTTP inbox stays in the base skeleton (`controllers/`, FRAMEWORK 6), because its path is not in this module's openapi.yaml and every runtime needs it. Open for the spec: name the hub role in README 3 or move it to the event bus of FRAMEWORK 6.
6. **FRAMEWORK 6, who may deliver an event.** The inbox accepts an event only with the token of the publishing module's service account. The hub therefore delivers with that token (`portal_common.tokens.service_token(<source module>)`), which needs the client secret of every service account in the hub's runtime (in this installation all share `SERVICE_CLIENT_SECRET`). Open: a relay permission for `svc-c12-m1` in the spec, so the hub can deliver with its own token.
7. **Routing per event type.** The spec has no list of the events each module consumes, so the hub routes every event to every runtime that serves a feature with `on_event`; the consumers ignore the types they do not handle. A list of consumed types (or broker topics) would let the hub filter.

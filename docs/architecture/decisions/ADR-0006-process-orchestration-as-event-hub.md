# ADR-0006: Process Orchestration as the event hub of a split installation

**Status:** proposed (17 Nov 2026)
**Requested by:** Mathias Moser (@matbmoser)
**Builds on:** [ADR-0001](ADR-0001-events-as-cloudevents.md) (CloudEvents, event inbox),
[ADR-0002](ADR-0002-runtime-per-module.md) (one image, many runtimes, `EVENT_SINKS`),
[ADR-0003](ADR-0003-feature-first-layout-and-runtimes.md) (features and runtimes),
[ADR-0004](ADR-0004-internal-boundaries-and-quality-gate.md) (layers and quality gate),
[ADR-0005](ADR-0005-cloud-native-database-provisioning-and-domain-clusters.md) (domain clusters, `operations`).

## Context

Process Orchestration (C12-M1, `features/process_orchestration/`) starts and continues flows on the events of all
other modules (C12-M1 README 1, 4, 6.5). In the modular monolith it gets every event from the in-memory relay. When
the installation is split into runtimes (ADR-0002, ADR-0005), three separate layers carried events and none of them
owned the routing:

- the event inbox `POST /api/v1/events/inbox` (`controllers/`) puts a received CloudEvent on the local bus;
- the relay (`portal_common.events`) delivers to every local subscriber and makes no routing decision;
- the forwarder (`portal_common.event_forwarder`) posts every locally published event to every address in
  `EVENT_SINKS`, a full mesh that each runtime has to list.

Process Orchestration was only one subscriber. It received the events of another runtime only if that runtime listed
it in `EVENT_SINKS`; a missing entry silently stopped every flow. Every runtime posted every event to every other
runtime, and a runtime that listed itself delivered its own events twice.

## Decision

1. **Process Orchestration is the event hub.** In a split installation every runtime delivers the events it publishes
   to the runtime of C12-M1. The forwarder finds it with the neighbour rule of FRAMEWORK 4.7 (`C12_M1_URL`,
   `MODULE_URLS`, `portal_common.neighbours`), so no extra variable is needed: when C12-M1 is `in-process` (the
   monolith, or the hub's own runtime) or a stand-in, nothing is posted. `EVENT_SINKS` still adds further inboxes
   (backward compatible, ADR-0002); the forwarder never posts to its own `BASE_URL`.
2. **The hub routes.** `features/process_orchestration/__init__.py` `on_event` receives every event of its runtime,
   whether published there or received through the inbox. It first routes the event on (`services/event_hub.py`,
   `managers/event_routes.py`), then runs the engine (README 6.5). The routing targets are the runtimes of the
   subscribing modules: the features whose index has `on_event` (`portal_common.layout.subscribers()`), addressed by
   the same neighbour rule. The hub skips subscribers in its own runtime (the relay delivered there already) and
   stand-ins, it does not send an event back to the runtime of its publisher (that relay delivered it there), and it
   sends to each runtime once.
3. **Same contract for transport.** The hub delivers through the forwarder (worker threads, retries, bounded queue)
   to the same inbox, with the service token of the publishing module (`svc-<module>`). The receiving inbox checks the
   event as if the publisher had sent it (FRAMEWORK 6: token, `source`, `type`), so the inbox contract, its Problem
   Details `urn:events:problem:*` and the 202 semantics do not change, and a runtime cannot tell whether an event came
   from the publisher or through the hub.
4. **The inbox endpoint stays in the base skeleton.** FRAMEWORK 6 defines the event inbox as part of the base
   skeleton of the installation ("not a module") at `/api/v1/events/inbox`, outside the base path of C12-M1 and not
   in its `openapi.yaml`; `portal_common.routing.mount()` and the contract check of ADR-0004 refuse such an operation
   in a feature. Every runtime also needs it as the receiving end of the hub. So `controllers/` keeps the HTTP binding
   (content modes, size limit, token, publisher checks); in the hub's runtime it is the inbox of the hub. It makes no
   routing decision; the relay hands its events to the hub like any other.
5. **No loops, delivered once.** Events received through the inbox are never forwarded by the relay; only the hub
   routes them on. The relay remembers the `source` and `id` of the events it published as well as those it received,
   so a copy that comes back (a second hub, a sink that points back) is answered with 202 and not delivered again.
6. **Modules do not change.** Features keep `events.publish(MODULE, type, data)` and `on_event(event)`; they do not
   know the hub (FRAMEWORK 1: modules do not know Process Orchestration). In the monolith every subscriber is
   in-process: delivery stays in memory, nothing leaves the process.

## Alternatives

| Option | Why not |
|---|---|
| Keep the full mesh of `EVENT_SINKS` | Every runtime must list every other; a missing entry silently stops the flows; N x (N - 1) posts per event. |
| Move the inbox endpoint into the feature | It is the base skeleton of FRAMEWORK 6 under `/api/v1`, not an operation of C12-M1; every runtime needs it to receive the hub's deliveries. |
| A dedicated relay service account (`svc-c12-m1` delivers for every module) | Changes the inbox contract of FRAMEWORK 6 (the token must match `source`); kept as an open point. |
| Subscriptions per event type at the hub | Needs a list of the consumed types of each module that the spec does not have yet; runtimes with subscribers get every event, consumers already ignore what they do not handle. |
| A broker (Kafka, NATS) now | Still the target for durability (ADR-0002); the hub keeps the CloudEvents HTTP binding until then and can be replaced by a broker topic without a change to the modules. |

## Consequences

- A split installation needs only `MODULE_URLS` (or `C12_M1_URL`) to connect its events; `EVENT_SINKS` becomes
  optional. Posts per event drop from one per runtime to one to the hub plus one per runtime with subscribers.
- The runtime of Process Orchestration (`operations`, ADR-0005) is on the path of every event between runtimes. If it
  is down, events between other runtimes wait in the forwarders' retries and are lost after the last attempt, as before
  (delivery is at least once, not durable; ADR-0002). A durable outbox or a broker remains the follow-up.
- The hub holds the tokens of the service accounts of the publishing modules to deliver on their behalf; in this
  installation all service accounts use the same client secret (`SERVICE_CLIENT_SECRET`), so no new credential is
  added. A dedicated relay permission is an open point (C12-M1 `OPEN-QUESTIONS.md`).
- The spec places the transport of events outside C12-M1 (C12-M1 README 3, FRAMEWORK 1). The hub is a deployment role
  of the feature and does not change its API, events or flows; the deviation is recorded in
  `features/process_orchestration/OPEN-QUESTIONS.md` for the spec authors.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-services/blob/main/docs/architecture/decisions/ADR-0006-process-orchestration-as-event-hub.md

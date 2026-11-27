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
 that the code is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# Notifications (C11-M1)

Migrated from `modules/c11_m1/` (spec `spec/C11-M1-Notifications`).

## What it does

The feature informs people in the portal of the OSP. It listens to the events that the other modules publish,
decides with a fixed set of rules (R1 to R17, spec README 6.2) who is informed, and keeps an inbox per person:
information (topic `INFO`) and tasks (topic `ACTION`) that are closed automatically when the matching event
arrives. No module calls it or knows it; they only publish their events.

Callers:

- people of a company and applicants (UI): read the own inbox, mark as read or unread, hide, follow new
  notifications as a Server-Sent Events stream;
- OSP staff (UI): the same, including the staff tasks of their permissions (for example `review_application`);
- the event relay of the installation (in-process, or the event inbox `POST /api/v1/events/inbox` when the
  feature runs in its own pod, routed on by Process Orchestration as the event hub, ADR-0006): delivers the
  CloudEvents of the other modules to `on_event()`.

It has no steps or queries for Process Orchestration and no other feature calls it.

## How it works

**One event in** (`services/engine.py`, the index's `on_event()`):

1. an event whose `source` and `id` were seen before is dropped (at-least-once delivery, README 6.4);
2. `services/closing.py` closes the open tasks this event closes and remembers it as a closer for 24 hours, so a
   task whose closing event arrived first is created `done`;
3. the applicant of `ApplicationSubmitted` is remembered (and forgotten when the application has ended);
4. every rule of the event `type` that is not switched off (`DISABLED_RULES`) creates its notifications:
   applicant and staff notifications are stored at once; notifications for people with a role in a company need
   a neighbour call, so they run as a job of the background `worker`, retried while the neighbour is unreachable
   (5 s, doubling, at most 10 minutes and 10 attempts).

A part that fails marks the event `FAILED` without stopping the other parts. Logs carry rule and event ids only,
never `content`.

**The inbox of a person**: personal notifications with the caller's `sub`, plus staff notifications whose
permission is in the token. Read and hidden are kept per person; an open task cannot be hidden (409 `task-open`).

**Folders**

| Folder | Content |
|---|---|
| `controllers/notifications/` | `GET /api/notifications/notifications` (list with filters and paging), `/count`, `/events` (stream), `/{notificationId}`, `POST /{notificationId}/read`, `/unread`, `/hide` |
| `services/` | `rules` (the table R1 to R17), `engine` (one event in), `closing` (tasks done), `recipients` (who gets a personal notification), `inbox` (what a person sees), `listing` (filters, sorting, paging), `marks` (read and hidden) |
| `managers/` | `store` (the repository of the tables, the only code that opens a database session; the stream broker), `worker` and `retry` (background delivery), `config` (`DISABLED_RULES`), `neighbour_client` (C2-M2 `list_company_user_refs`, C10-M1 `find_subscriptions` and `get_subscription_internal`), `company_users_standin` with `data/stub-company-users.json` (the built-in stand-in of C2-M2) |
| `models/` | `MODULE`, the `Rule` type, the Problem factories (`errors.py`: `not-found`, `task-open`), the pydantic models (`notification.py`: `Notification`, `NotificationPage`, `NotificationCount`, the stream events `NotificationCreated` and `NotificationDone`, and `StoredNotification`, the form the services use) and the SQLModel tables of README 5 (`tables.py`: `notification`, `notification_state`, `applicant`, `processed_event`, `dedup_key`) |

**Interface**: `interface.py` has no steps or queries of the spec (README 8 and 9; any such call gets the scaffold
fallback). It holds the inbox operations of README 7 (`list_notifications`, `count_notifications`,
`get_notification`, `mark_read`, `mark_unread`, `hide_notification`, the stream broker and its filter), which
the controllers call.

**Events**: consumes the events of spec README 11.1 (applications, change requests, offers, subscriptions,
wallets, credentials, connectors, process steps). It publishes no CloudEvents; the stream events
`notification-created` and `notification-done` go to the browsers of the inbox owners only.

**Configuration** (read at call time): `DISABLED_RULES` (`managers/config.py`), and the neighbour addresses
`C2_M2_URL` and `C10_M1_URL` (or `MODULE_URLS`, `portal_common.neighbours`): empty means the built-in stand-in
(C2-M2 from the stand-in file, C10-M1 an empty list). `RETENTION_DAYS` is not applied yet (OPEN-QUESTIONS.md 1).

**Persistence**: the tables of `models/tables.py` in the feature's own database (`portal_common.database`):
`NOTIFICATIONS_DATABASE_URL`, then `C11_M1_DATABASE_URL`, then `DATABASE_URL`; without one a private in-memory
SQLite database, so a restart loses the data. `on_startup()` creates the tables, `reset()` empties them. The
remembered closing events (24 hours), the queued delivery jobs and the replay buffer of the stream stay in memory.
At most 10 000 processed events and dedup keys are kept, the oldest are dropped first.

**Run and test**

```bash
RUNTIME=notifications uv run python -m runtimes      # the feature alone, port 8000 (PORT)
uv run pytest -q tests/test_c11_m1_*.py tests/test_sse.py
```

## Links

- Spec: [README](../../spec/C11-M1-Notifications/README.md), [openapi.yaml](../../spec/C11-M1-Notifications/openapi.yaml)
- [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)
- [ADR-0003](../../docs/architecture/decisions/ADR-0003-feature-first-layout-and-runtimes.md), [features/AGENTS.md](../AGENTS.md)

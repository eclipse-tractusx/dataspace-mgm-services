<!--
Copyright (c) 2026 Technovative Solutions
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

# C11-M1 Notifications: open questions

Points where the spec (`spec/C11-M1-Notifications/README.md`, as of 19 Nov 2026, commit
[`abab1fa`](https://github.com/tx-arena-events/portal-backend-spec/tree/abab1fa)) leaves a choice or where this
implementation differs from it. A spec change goes to the spec repository, not here.

| No. | Question | Spec | What this implementation does |
|---|---|---|---|
| 1 | Persistence | README 4, 5; FRAMEWORK 4.9 | The tables of README 5 (`models/tables.py`) in the feature's own database (`NOTIFICATIONS_DATABASE_URL`); without a URL an in-memory SQLite database, so a restart loses the data. Remembered closing events, queued jobs and the stream replay stay in memory. A runtime with several features doesn't start with only `DATABASE_URL` ([#110](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/110)). Three differences from the spec: the code also reads the interim `C11_M1_DATABASE_URL`; every start empties the tables, also with a URL ([#101](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/101)); `RETENTION_DAYS` is not applied yet ([#104](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/104)). |
| 2 | Subject and company of each rule | README 5 (`subject_type`, `subject_id`, `company_id`), 6.2 | 6.2 does not name them per rule. `services/rules.py` sets them per rule: the object the rule is about (for example `OFFER` / `offerId` for R6 to R8, `COMPANY` / `companyId` for R15), and the company field the recipients come from. |
| 3 | `companyId` without a company field | README 5 | R12, R13 and R17 events carry no company field that the rule uses, so `companyId` is empty (`null`). |
| 4 | `done` of an information | README 5, openapi `Notification.done` | `null` for topic `INFO`, in 7.1 and in `notification-created`; `true`/`false` only for tasks. |
| 5 | Delivery that keeps failing | README 4 | Only an unreachable neighbour (a `retryable` problem) is retried; after 10 attempts the job is logged as not delivered (rule id and event id only). A neighbour that rejects the call (4xx) is not retried: the job is logged at once as failed, with the error. The event keeps `processed_event.status` `DONE`, because the event itself was processed. |
| 6 | Remembered closing events | README 6.2 | Kept 24 hours in memory. An event without `time` counts as received now. |
| 7 | `applicantSub` in `content` | README 5 (`content`: "never names") | `content` is the whole `data` of the event, so R2 (a staff task) carries the `sub` of the applicant. It is an ID, not a name, and the reviewer needs no person data; to be confirmed. |
| 8 | Second approval of an offer | OP-49 | No event exists for it, so there is no notification. |
| 9 | Staff permission removed while a stream is open | README 7.6 | The stream uses the permissions of the token that opened it until `exp`; the next token decides. |
| 10 | Reading a hidden notification | README 7.1, 7.3 | 7.1 leaves hidden notifications out of the list; 7.3 says nothing. `GET /notifications/{id}` still returns a hidden notification of the own inbox. |
| 11 | Marking as read twice | README 6.4, 7.4 | Idempotent: the second call keeps the time of the first read. |
| 12 | Filter `done` | README 7.1 ("tasks only") | With `done` set, the list contains tasks only; information notifications are left out. |
| 13 | `createdSince` without a time zone | README 7.1, FRAMEWORK 4.1 | Counts as UTC. |
| 14 | Names of the neighbour addresses | README 4, FRAMEWORK 4.7 | README 4 names `APP_ACCESS_URL` (C2-M2) and `SUBSCRIPTION_URL` (C10-M1). The scaffold has one notation for every module, read by `portal_common.neighbours`: `<MODULE>_URL` (`C2_M2_URL`, `C10_M1_URL`), then `MODULE_URLS`, then `MODULE_URLS_DEFAULT` (`docs/developers/hackathon-scaffold.md`). C11-M1 follows the scaffold; `AGENTS.md` rule 6 documents that `portal_common.neighbours` doesn't read the names of section 4 yet and that a feature doesn't read a neighbour's address itself. |
| 15 | `done_at` of a task | README 5, 6.2 | A task closed by its closing event gets that event's `time`, converted to UTC (FRAMEWORK 4.1). A task created as done, because its closing event arrived first, gets the time it was stored. |
| 16 | Base path | FRAMEWORK 4.1, 4.9; OP-55 | Decided by OP-55 (17 Nov 2026): the spec itself now defines the base path `/api/notifications`, and `/api/c11-m1` answers 404. Problem types (`urn:c11-m1:problem:...`), event sources, permissions, the log name `portal.c11-m1` and the service account `svc-c11-m1` keep the spec id. |
| 17 | An ID field that is not a string | README 5, FRAMEWORK 4.1 | `companyId` and `subjectId` are stored only when the event field is a string (the columns hold IDs); any other value gives `null`. `content` keeps the event data as it is. |
| 18 | Column types and keys | README 5 | The columns are text where README 5 names `uuid` and `timestamptz`, and `content` is SQLAlchemy `JSON` (`json` on PostgreSQL), not `jsonb`. `notification` and `processed_event` have an integer key `seq`; the dedup key is a table of its own (`dedup_key`, at most 10 000 rows); `processed_event` has `type`, not `event_type` ([#105](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/105)). An event is identified by its `source` and `id`, not by `id` alone, as CloudEvents and the event inbox of FRAMEWORK 6 do (proposed for the spec in [portal-backend-spec#5](https://github.com/tx-arena-events/portal-backend-spec/issues/5)). |

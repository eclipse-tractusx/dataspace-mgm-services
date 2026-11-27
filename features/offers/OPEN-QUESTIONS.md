<!--
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

# C8-M1 open questions

The feature is still the stand-in of the hackathon core path; the open points of the spec are in
`spec/C8-M1-Offers/open-points.md`.

1. **FRAMEWORK 4.1, base path `/api/c8-m1`** "until the common path convention is settled". Implemented: served under the readable feature name `/api/offers` (ADR-0003, decision 2); `/api/c8-m1` answers 404. Problem types, event sources, permissions and the service account `svc-c8-m1` keep the spec id.
2. **README 6.1, status of a draft.** The schema `OfferStatus` names it `CREATED`; the stand-in answers `DRAFT` (as before the migration, `models/offer.py`), and has no `INACTIVE` yet. To decide when the stand-in is replaced by the real module.
3. **Validation of the stand-in.** It is more lenient than `openapi.yaml`, unchanged by the migration: `name` needs 1 character (schema: 3), `descriptions` of an `AppRole` may be left out (schema: at least one), and further fields of `OfferInput` are accepted but not stored.

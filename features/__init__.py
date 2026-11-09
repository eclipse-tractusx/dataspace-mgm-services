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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Features of the Dataspace Management Service, one package per feature (ADR-0003).

Every feature has the same shape, so a reader finds the same thing in the same place:

    features/<feature>/
        __init__.py      index: NAME, MODULE (spec id) and the lifecycle hooks reset(), on_startup(), on_event()
        router.py        `router = mount(controllers, MODULE)`: the controller tree under the base path
        main.py          the feature as its own runtime (one pod)
        interface.py     in-process contract (call convention): the steps and queries other features call
        controllers/     HTTP only, one folder per path segment of the API; `controller.py` per folder
        services/        business logic, shared by the controllers and the interface; no HTTP
        managers/        state and adapters: repositories, storage backends, clients of neighbours
        models/          value sets and data models of the API (when the feature has its own)

The feature name is the readable name of the spec folder (`C1-M2-Registration` -> `registration`);
the spec id stays at the edge only (`/api/c1-m2`, `urn:c1-m2:problem:...`, `svc-c1-m2`). Runtimes in
`runtimes/` import features and serve one or several of them. A spec module without a feature folder
still runs from its hackathon folder `modules/<id>/`.
"""

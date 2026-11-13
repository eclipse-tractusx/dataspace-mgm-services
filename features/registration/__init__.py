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
"""Registration (spec C1-M2): a company applies to join the dataspace.

The applicant fills in the application, proves the company with an attestation of the business wallet or with
documents, accepts the agreements and submits; Process Orchestration completes or closes it.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()` and `on_startup()`. The HTTP API is `features.registration.router.router`.
"""
from __future__ import annotations

from features.registration.managers import application_repository, reference_catalog
from features.registration.services import attestation_verifier
from features.registration.services.shared import MODULE

NAME = "registration"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def reset() -> None:
    with application_repository.applications_lock:
        application_repository.reset()
        reference_catalog.reset()
        attestation_verifier.reset()


def on_startup() -> None:
    attestation_verifier.config()   # an invalid value prevents the start (README 4)
    reference_catalog.master()

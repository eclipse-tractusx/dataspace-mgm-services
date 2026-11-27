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
"""CSP Connection (spec C3-M2): the only place through which an installation uses the core services of the CSP.

Registers companies with the CSP (BPN, home OSP), checks for duplicates, keeps the membership, the directory
BPN -> DID and the connectors in the discovery of the CSP, and receives the notifications of the CSP.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `on_startup()` (tables and seed data) and `reset()` (empty tables plus seed data, README 4). The HTTP
API is `features.csp_connection.router.router`.
"""
from __future__ import annotations

from features.csp_connection import services
from features.csp_connection.models.errors import MODULE

NAME = "csp_connection"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def reset() -> None:
    services.reset()


def on_startup() -> None:
    services.start()

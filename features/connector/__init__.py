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
"""Connector (spec C6-M1): the register of the connectors of the companies of this installation (README 5),
company connectors and connectors as a service, with the steps for Process Orchestration (README 8) and the
query for C2-M3 (README 9). The register is in the feature's own database (`portal_common.database`).

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hook a runtime
calls, `on_startup()` and `reset()`. The HTTP API is `features.connector.router.router`.
"""
from __future__ import annotations

from features.connector import services
from features.connector.models import MODULE

NAME = "connector"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def on_startup() -> None:
    services.start()


def reset() -> None:
    services.reset()

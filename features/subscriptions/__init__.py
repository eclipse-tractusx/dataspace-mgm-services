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
"""Subscriptions (spec C10-M1): subscriptions of a company to the offers of a provider, app path of
FRAMEWORK 5.8 (provider configuration, subscribe, start setup, activate) and the steps `notify-provider` and
`send-activation-callback` of Process Orchestration.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `on_startup()` and `reset()`. The HTTP API is `features.subscriptions.router.router`.
"""
from __future__ import annotations

from features.subscriptions import services
from features.subscriptions.models.subscription import MODULE
from portal_common import database

NAME = "subscriptions"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def on_startup() -> None:
    database.create_tables(MODULE)


def reset() -> None:
    services.reset()

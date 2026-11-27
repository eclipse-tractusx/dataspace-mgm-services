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
"""App Access (spec C2-M2 Users and App Access): the accounts of people in the Portal IAM of the OSP (binding to a
company, portal roles, app roles), invitations, the OSP staff, and the clients of the apps with their app roles.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()` and `on_startup()`. The HTTP API is `features.app_access.router.router`.
"""
from __future__ import annotations

from features.app_access.models.utils import MODULE
from features.app_access.services import module

NAME = "app_access"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def reset() -> None:
    module.reset()


def on_startup() -> None:
    module.on_startup()

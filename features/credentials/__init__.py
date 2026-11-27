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
"""Credentials (spec C4-M1): the BPN and membership credentials of a company, triggered at an issuer through
one of the routes of README 6.3, and their revocation.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `on_startup()` (creates the tables) and `reset()` (empties them). The HTTP API is
`features.credentials.router.router`.
"""
from __future__ import annotations

from features.credentials.models.errors import MODULE
from features.credentials.services import credential_service
from portal_common import database

NAME = "credentials"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def on_startup() -> None:
    """Creates the tables of README 5 in the feature's database when they do not exist yet."""
    database.create_tables(MODULE)


def reset() -> None:
    """Empties the tables, cancels pending STUB timers, clears the routes state."""
    credential_service.reset()

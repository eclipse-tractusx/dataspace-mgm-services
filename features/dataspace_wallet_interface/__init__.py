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
"""Dataspace Wallet Interface (spec C4-M2): the dataspace wallet of every company and the wallet accounts of its
technical users, vendor-neutral with one adapter per provider (SAP DIV, IdentityHub, CSP).

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()` and `on_startup()`. The HTTP API is `features.dataspace_wallet_interface.router.router`.
"""
from __future__ import annotations

from features.dataspace_wallet_interface import interface
from features.dataspace_wallet_interface.models import MODULE
from features.dataspace_wallet_interface.services import wallet_service
from portal_common import database

NAME = "dataspace_wallet_interface"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def reset() -> None:
    """Empty tables (`database.reset_tables` through the store), key cache and provider stand-ins."""
    interface.reset()


def on_startup() -> None:
    """Create the tables of the feature's database and start the scheduled tasks of README 6.10."""
    database.create_tables(MODULE)
    wallet_service.start_timer()

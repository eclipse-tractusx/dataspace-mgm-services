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
"""Business logic of the connectors: the operations of people (`connectors`, README 7), the steps (`steps`,
README 8) and the query (`queries`, README 9). No HTTP; the controllers pass the calling company and person."""
from __future__ import annotations

from ..managers import connector_repository as _repository
from ..managers import neighbour_client as _neighbour_client
from .connectors import (
    change_endpoint,
    delete_connector,
    get_connector,
    list_connectors,
    register_connector,
    register_connector_as_a_service,
)
from .queries import list_connectors_internal
from .steps import deactivate_subscription_connectors, unlink_technical_user


def start() -> None:
    """Creates the tables of the feature's database (start-up)."""
    _repository.create_tables()


def reset() -> None:
    """Empty register and audit log, stand-in data as in `managers/data/`."""
    _repository.reset()
    _neighbour_client.reset_standins()


__all__ = [
    "change_endpoint", "deactivate_subscription_connectors", "delete_connector", "get_connector", "list_connectors",
    "list_connectors_internal", "register_connector", "register_connector_as_a_service", "reset", "start",
    "unlink_technical_user",
]

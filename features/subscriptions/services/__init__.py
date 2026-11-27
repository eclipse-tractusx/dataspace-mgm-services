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
"""Business logic of the subscriptions, without HTTP: called by the controllers and by `interface.py`."""
from __future__ import annotations

from features.subscriptions.models.subscription import MODULE
from features.subscriptions.services.provider_configuration import put_provider_configuration
from features.subscriptions.services.queries import find_subscriptions, get_subscription_internal
from features.subscriptions.services.steps import notify_provider, send_activation_callback
from features.subscriptions.services.subscriptions import activate, get_subscription, start_setup, subscribe
from portal_common import database

__all__ = ["activate", "find_subscriptions", "get_subscription", "get_subscription_internal", "notify_provider",
           "put_provider_configuration", "reset", "send_activation_callback", "start_setup", "subscribe"]


def reset() -> None:
    """Empty tables (tests, `/scaffold/reset`)."""
    database.reset_tables(MODULE)

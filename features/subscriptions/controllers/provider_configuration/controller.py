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
"""Configuration of a provider (setup and callback addresses, token client)."""
from __future__ import annotations

from features.subscriptions import interface
from features.subscriptions.models.provider_configuration import ProviderConfiguration, ProviderConfigurationInput
from portal_common.routing import Controller, Permission

controller = Controller("Subscriptions: Provider Configuration")


@controller.put("", response_model=ProviderConfiguration)
def put_config(body: ProviderConfigurationInput, claims: dict = Permission) -> ProviderConfiguration:
    return interface.put_provider_configuration(claims.get("company_id"), body)

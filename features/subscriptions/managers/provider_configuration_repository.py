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
"""The provider configurations in the feature's database, with their secrets; never returned over the API."""
from __future__ import annotations

from features.subscriptions.models.provider_configuration import StoredProviderConfiguration
from features.subscriptions.models.subscription import MODULE
from features.subscriptions.models.tables import ProviderConfigurationRow
from portal_common import database


def save(configuration: StoredProviderConfiguration) -> None:
    """Insert or replace the configuration of the provider company."""
    with database.session(MODULE) as session:
        session.merge(ProviderConfigurationRow(**configuration.model_dump(by_alias=False)))


def get(company_id: str) -> StoredProviderConfiguration | None:
    with database.session(MODULE) as session:
        row = session.get(ProviderConfigurationRow, company_id)
        return StoredProviderConfiguration.model_validate(row, from_attributes=True) if row else None

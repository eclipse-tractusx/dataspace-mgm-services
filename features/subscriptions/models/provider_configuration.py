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
"""The provider configuration (7.9): where and with which client the subscriptions call the provider's system."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field

from portal_common.models import ApiModel, RequestBody, Uuid

NonEmpty = Annotated[str, Field(min_length=1)]


class ProviderConfigurationInput(RequestBody):
    """PUT body. The stand-in needs all five fields (OPEN-QUESTIONS 4): it calls both URLs and keeps no old secret."""

    setup_url: NonEmpty
    callback_url: NonEmpty
    token_url: NonEmpty
    client_id: NonEmpty
    client_secret: NonEmpty


class ProviderConfiguration(ApiModel):
    """The configuration as the provider reads it back: never the secret, only whether one is set."""

    company_id: Uuid
    setup_url: str | None = None
    callback_url: str | None = None
    token_url: str
    client_id: str
    client_secret_set: bool
    updated_at: datetime


class StoredProviderConfiguration(ProviderConfigurationInput):
    """What the stand-in keeps in memory, with the secret."""

    company_id: Uuid
    updated_at: datetime

    def public(self) -> ProviderConfiguration:
        return ProviderConfiguration(client_secret_set=bool(self.client_secret),
                                     **self.model_dump(exclude={"client_secret"}))

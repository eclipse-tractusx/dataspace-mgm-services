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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""Credential issuance request accepted from the onboarding caller."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CredentialIssuanceRequest(BaseModel):
    """Credential details; wallet access is resolved from C4-M2 by company ID."""

    model_config = ConfigDict(extra="forbid")

    company_id: str = Field(min_length=1)
    issuer_did: str = Field(min_length=1)
    holder_pid: str = Field(min_length=1)
    credential_definition: str = Field(min_length=1)
    credential_type: str | None = None
    credential_format: str = Field(min_length=1)
    identity_api_version: str | None = Field(default=None, min_length=1)

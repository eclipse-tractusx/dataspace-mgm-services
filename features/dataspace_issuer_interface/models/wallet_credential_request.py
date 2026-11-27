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
"""Wallet-side credential request payload for DCP initiation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class WalletCredentialRequest(BaseModel):
    """The one issuance-trigger request sent to the holder wallet."""

    model_config = ConfigDict(extra="forbid")

    identity_api_url: str = Field(min_length=1)
    identity_api_version: str | None = Field(default=None, min_length=1)
    participant_context_id: str = Field(min_length=1)
    api_key: SecretStr = Field(min_length=1, repr=False)
    issuer_did: str = Field(min_length=1)
    holder_pid: str = Field(min_length=1)
    credential_definition: str = Field(min_length=1)
    credential_type: str | None = None
    credential_format: str = Field(min_length=1)

    def to_json(self) -> dict[str, object]:
        return {
            "issuerDid": self.issuer_did,
            "holderPid": self.holder_pid,
            # The wallet sends only `id` to the issuer, which resolves it as a credential definition.
            "credentials": [
                {
                    "id": self.credential_definition,
                    "type": self.credential_type or self.credential_definition,
                    "format": self.credential_format,
                }
            ],
        }

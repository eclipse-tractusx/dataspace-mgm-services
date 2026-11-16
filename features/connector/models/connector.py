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
"""The models of openapi.yaml of C6-M1: value sets, request bodies, step inputs and responses.

The request bodies check the shape and the formats of the spec (types, lengths, `Uuid`, `CountryCode`). They
accept unknown fields, as openapi.yaml does not set `additionalProperties: false`. The rules that need more
than the shape (HTTPS endpoint, the country list of the installation) are checks of `services/connectors.py`.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from portal_common.models import ApiModel, CountryCode, StepRequest, Uuid

MODULE = "c6-m1"


class ConnectorType(StrEnum):
    COMPANY_CONNECTOR = "COMPANY_CONNECTOR"
    CONNECTOR_AS_A_SERVICE = "CONNECTOR_AS_A_SERVICE"


class ConnectorStatus(StrEnum):
    """README 6.1."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Role(StrEnum):
    """Filter of 7.1: connectors the own company runs (`provider`) or that a provider runs for it (`host`)."""
    PROVIDER = "provider"
    HOST = "host"


ACTIVE, INACTIVE = ConnectorStatus.ACTIVE.value, ConnectorStatus.INACTIVE.value
COMPANY_CONNECTOR = ConnectorType.COMPANY_CONNECTOR.value
CONNECTOR_AS_A_SERVICE = ConnectorType.CONNECTOR_AS_A_SERVICE.value


# ---------------------------------------------------------------- requests (README 7)
class ConnectorInput(ApiModel):
    """`ConnectorInput` (7.2)."""
    name: str = Field(min_length=1, max_length=255)
    endpoint: str
    location: CountryCode
    technical_user_id: Uuid | None = None


class ConnectorAsAServiceInput(ConnectorInput):
    """`ConnectorAsAServiceInput` (7.3)."""
    offer_subscription_id: Uuid


class EndpointChange(ApiModel):
    """Body of 7.5."""
    endpoint: str


# ---------------------------------------------------------------- steps (README 8)
class DeactivateSubscriptionConnectorsInput(StepRequest):
    offer_subscription_id: Uuid


class UnlinkTechnicalUserInput(StepRequest):
    technical_user_id: Uuid


class ConnectorIds(ApiModel):
    """`result` of both steps: the connectors this call changed."""
    connector_ids: list[str]


# ---------------------------------------------------------------- responses
class Connector(ApiModel):
    """`Connector`; built from a row with `Connector.model_validate(row, from_attributes=True)`."""
    connector_id: str
    name: str
    endpoint: str
    location: str
    type: ConnectorType
    status: ConnectorStatus
    provider_company_id: str
    host_company_id: str
    technical_user_id: str | None = None
    offer_subscription_id: str | None = None
    created_at: str
    changed_at: str | None = None


class ConnectorRef(ApiModel):
    """`ConnectorRef` (9.1)."""
    connector_id: str
    status: ConnectorStatus

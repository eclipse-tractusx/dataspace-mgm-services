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
#  Assisted-By: GitHub Copilot (Claude Sonnet 5.5)
#################################################################################
"""Input of the operations and steps as in `openapi.yaml` (components/schemas); `models.validation.parse` turns a
failed check into 400 `validation`.

The models build on `portal_common.models` (snake_case in Python, camelCase in JSON). Input is strict and
accepted only under its JSON name, like the schema: `offer_subscription_id` in a body is an undeclared field."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, ConfigDict, Field, field_validator, model_validator

from portal_common.models import ApiModel, RequestBody, StepRequest, Uuid

_INPUT = ConfigDict(strict=True, validate_by_name=False)


class RoleRef(ApiModel):
    """A role by name, in requests and responses."""

    model_config = _INPUT

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("role name must not be blank")
        return value


def _unique(roles: list[RoleRef]) -> list[RoleRef]:
    if len({role.name for role in roles}) != len(roles):
        raise ValueError("role names must be unique")
    return roles


RoleList = Annotated[list[RoleRef], Field(min_length=1), AfterValidator(_unique)]


def role_refs(names: list[str]) -> list[RoleRef]:
    return [RoleRef(name=name) for name in names]


class _WithRoles:
    """The names of the `roles` field of a model."""

    @property
    def role_names(self) -> list[str]:
        return [role.name for role in self.roles or []]  # type: ignore[attr-defined]


class TechnicalUserCreate(_WithRoles, RequestBody):
    model_config = _INPUT

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    auth_method: Literal["SECRET"] | None = None
    roles: RoleList


class TechnicalUserUpdate(_WithRoles, RequestBody):
    model_config = _INPUT

    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    roles: RoleList | None = None

    @model_validator(mode="after")
    def _something_to_change(self) -> TechnicalUserUpdate:
        if not self.model_fields_set:
            raise ValueError("provide name, description, or roles")
        return self


class SubscriptionCredentialsRequest(RequestBody):
    model_config = _INPUT

    offer_subscription_id: Uuid


class _Step(StepRequest):
    """`processId` and `stepRunId` are required by openapi.yaml (StepRequest); they only serve the audit log."""

    model_config = _INPUT


class StepCreateForSubscription(_WithRoles, _Step):
    customer_company_id: Uuid
    provider_company_id: Uuid
    offer_subscription_id: Uuid
    name: str = Field(min_length=1, max_length=200)
    roles: RoleList


class StepApplyWalletAccess(_Step):
    technical_user_id: Uuid
    outcome: Literal["ACTIVE", "FAILED"]
    wallet_account_ref: str | None = None

    @model_validator(mode="after")
    def _active_needs_a_reference(self) -> StepApplyWalletAccess:
        if self.outcome == "ACTIVE" and not self.wallet_account_ref:
            raise ValueError("outcome ACTIVE requires walletAccountRef")
        return self


class StepTechnicalUserRef(_Step):
    technical_user_id: Uuid


class StepCompanyRef(_Step):
    company_id: Uuid


class StepSubscriptionRef(_Step):
    offer_subscription_id: Uuid

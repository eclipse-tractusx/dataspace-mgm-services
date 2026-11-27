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
"""Results of the steps of README 8 inside the step envelope `StepResult[T]` (FRAMEWORK 4.4)."""
from __future__ import annotations

from features.company_profile.models.value_sets import CompanyStatus, CoreDataSource, DeactivationReason
from portal_common.models import ApiModel, StepResult


class CompanyState(ApiModel):
    """8.4: the state of the company after the step."""

    company_id: str
    status: CompanyStatus


class CreatedCompany(CompanyState):
    """8.1"""

    bpn: str | None = None
    core_data_source: CoreDataSource


class AssignedIdentifier(CompanyState):
    """8.2"""

    bpn: str


class Activation(CompanyState):
    """8.3: the roles activated now and the roles still waiting for a consent."""

    bpn: str | None = None
    company_roles: list[str]
    pending_company_roles: list[str]


class Deactivation(CompanyState):
    """8.5"""

    deactivation_reason: DeactivationReason | None = None


class Reactivation(CompanyState):
    """8.6"""

    bpn: str | None = None
    company_roles: list[str]
    changed_fields: list[str]


def step_result[Result: ApiModel](input: dict, result: Result) -> StepResult[Result]:
    """The `DONE` envelope for a step input; `stepRunId` is echoed as it came."""
    return StepResult[type(result)](step_run_id=input.get("stepRunId"), result=result)

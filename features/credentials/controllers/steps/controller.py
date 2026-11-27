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
"""The steps of the credentials in the flows of Process Orchestration (README 8)."""
from __future__ import annotations

from features.credentials import interface
from features.credentials.models.credentials import IssueCredentials, IssueResult, RevocationResult, RevokeCredentials
from portal_common.models import StepResult
from portal_common.routing import Controller, Permission

controller = Controller("Credentials: Process Steps and Queries")


@controller.post("/issue-credentials", response_model=StepResult[IssueResult], response_model_exclude_none=True,
                 summary="Step: issue-credentials")
def issue(body: IssueCredentials, _: dict = Permission) -> StepResult[IssueResult]:
    return interface.issue(body)


@controller.post("/revoke-credentials", response_model=StepResult[RevocationResult],
                 response_model_exclude_none=True, summary="Step: revoke-credentials")
def revoke(body: RevokeCredentials, _: dict = Permission) -> StepResult[RevocationResult]:
    return interface.revoke(body)

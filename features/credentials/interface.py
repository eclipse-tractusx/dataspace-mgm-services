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
#  Assisted-By: Claude Code (claude-sonnet-5-5)
#################################################################################
"""In-process contract of the credentials (spec C4-M1, call convention of AGENTS.md).

- Steps and queries under their convention names: `issue_credentials(input)`, `revoke_credentials(input)` and
  `query_company_credentials(companyId=...)`, with the JSON of `openapi.yaml` (dicts) as input and answer, as over
  HTTP; an invalid input is 400 `validation`. `report_status()` serves an issuer in the same process.
- The operations of the controllers, with the API models of `models/credentials.py`.

Other modules and Process Orchestration import only from here; the rules are in `services/`, the storage and the
issuer clients in `managers/`.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from features.credentials.models.credentials import (
    CompanyCredentials,
    ConfirmRevocation,
    CredentialDetail,
    CredentialPage,
    CredentialStatusView,
    IssueCredentials,
    IssueResult,
    RevocationResult,
    RevokeCredentials,
    as_json,
)
from features.credentials.models.errors import MODULE, parse
from features.credentials.services import credential_service, credential_views
from portal_common.models import StepResult

__all__ = [
    "MODULE", "company_credentials", "confirm_revocation", "issue", "issue_credentials", "list_credentials",
    "own_credentials", "query_company_credentials", "receive_report", "report_status", "reset", "revoke",
    "revoke_credentials", "store",
]


# -- steps and queries (call convention): JSON in, JSON out ------------------------------------------------
def issue_credentials(input: dict) -> dict:
    """Step `issue-credentials` (README 8.1)."""
    return issue(parse(IssueCredentials, input)).to_json()


def revoke_credentials(input: dict) -> dict:
    """Step `revoke-credentials` (README 8.2)."""
    return revoke(parse(RevokeCredentials, input)).to_json()


def query_company_credentials(*, companyId: str) -> dict:
    """Query `query_company_credentials` (README 9.1)."""
    return as_json(company_credentials(companyId))


def report_status(kind: str, bpn: str, status: str, message: str | None = None) -> None:
    """README 7.4 steps 3 and 4: processes the status report of an issuer."""
    credential_service.report_status(kind, bpn, status, message)


# -- operations of the controllers: API models ------------------------------------------------------------
def issue(request: IssueCredentials) -> StepResult[IssueResult]:
    return credential_service.issue_credentials(request)


def revoke(request: RevokeCredentials) -> StepResult[RevocationResult]:
    return credential_service.revoke_credentials(request)


def company_credentials(company_id: str) -> CompanyCredentials:
    """README 9.1, as model."""
    return credential_views.query_company_credentials(companyId=company_id)


def own_credentials(company_id: str) -> list[CredentialStatusView]:
    """README 7.1: the credentials of the own company."""
    return credential_views.list_company_credentials(company_id)


def list_credentials(*, statuses: Sequence[str] | None, credential_type: str | None, company_id: str | None,
                     route: str | None, requested_before: dt.datetime | None, page: int, size: int) -> CredentialPage:
    """README 7.2: every credential, for OSP staff."""
    return credential_views.list_credentials(statuses=statuses, credential_type=credential_type,
                                             company_id=company_id, route=route, requested_before=requested_before,
                                             page=page, size=size)


def confirm_revocation(credential_id: str, request: ConfirmRevocation, claims: dict) -> CredentialDetail:
    """README 7.3: OSP staff confirm a revocation done by hand."""
    return credential_service.confirm_revocation(credential_id, request, claims)


def receive_report(kind: str, body: object, claims: dict) -> None:
    """README 7.4: a status report of an issuer over HTTP."""
    credential_service.receive_report(kind, body, claims)


# -- tests -----------------------------------------------------------------------------------------------
def store() -> credential_service.CredentialStore:
    """The active `CredentialStore`."""
    return credential_service.store()


def reset() -> None:
    """Empties the tables, cancels pending STUB timers, clears the routes state."""
    credential_service.reset()

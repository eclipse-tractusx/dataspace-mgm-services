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
"""Read views of the credentials (README 7.1, 7.2, 9.1): rows of the store as the API models of `openapi.yaml`."""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from features.credentials.managers import config
from features.credentials.managers.credential_store import store
from features.credentials.models.credentials import (
    CompanyCredentials,
    CredentialDetail,
    CredentialPage,
    CredentialStatusView,
    IssuanceRunView,
)
from features.credentials.models.values import TYPES, CredentialType


def _type_order(credential_type: str) -> int:
    """Position in the spec's order of the types; unknown types (from the configuration) last."""
    return TYPES.index(credential_type) if credential_type in TYPES else len(TYPES)


def _rows_of(company_id: str) -> list[dict]:
    rows = store().list_credentials(company_id=company_id, size=1000)
    return sorted(rows, key=lambda r: _type_order(r["credential_type"]))


def query_company_credentials(*, companyId: str) -> CompanyCredentials:
    """README 9.1: status per credential type and the last round; an unknown company gives an empty list."""
    run = store().get_run(companyId)
    return CompanyCredentials(company_id=companyId,
                              credentials=[CredentialStatusView.model_validate(r) for r in _rows_of(companyId)],
                              run=None if run is None else IssuanceRunView.model_validate(run))


def list_company_credentials(company_id: str) -> list[CredentialStatusView]:
    """README 7.1: no messages of the issuer, no routes; onboarding types without a row show `NONE`."""
    views = {r["credential_type"]: CredentialStatusView.model_validate(r) for r in _rows_of(company_id)}
    for t in config.onboarding_types():
        views.setdefault(t, CredentialStatusView(credential_type=CredentialType(t), status="NONE"))
    return [views[t] for t in sorted(views, key=_type_order)]


def list_credentials(statuses: Sequence[str] | None = None, credential_type: str | None = None,
                     company_id: str | None = None, route: str | None = None,
                     requested_before: dt.datetime | None = None, page: int = 0, size: int = 20) -> CredentialPage:
    """README 7.2: filters, sorted by `changedAt` descending, paged in the store."""
    if requested_before is not None and requested_before.tzinfo is None:
        requested_before = requested_before.replace(tzinfo=dt.UTC)
    filters = (company_id, statuses, credential_type, route, requested_before)
    rows = store().list_credentials(*filters, page=page, size=size)
    return CredentialPage(items=[CredentialDetail.model_validate(r) for r in rows], page=page, size=size,
                          total=store().count_credentials(*filters))

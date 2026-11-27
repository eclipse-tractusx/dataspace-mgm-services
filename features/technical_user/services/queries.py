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
"""Reading operations (README 7.1, 7.3, 7.9, 7.10 and 9.1); they change nothing."""
from __future__ import annotations

from collections.abc import Callable

from portal_common.models import Page

from ..managers.technical_user_repository import repository
from ..models import DEFAULT_LIST_STATUSES, TechnicalUserRecord, Viewer, validation
from ..models.responses import TechnicalUser, TechnicalUserCheck, TechnicalUserSummary
from . import accounts, projections, state


def _statuses(status: str | list[str] | None) -> list[str] | tuple[str, ...]:
    if status is None:
        return DEFAULT_LIST_STATUSES
    return [status] if isinstance(status, str) else list(status)


def _page(rows: list[TechnicalUserRecord], viewer: Callable[[TechnicalUserRecord], Viewer], *, page: int,
          size: int) -> Page[TechnicalUserSummary]:
    """The newest first; only the rows of the page become response models."""
    validation.validate_page(page, size)
    rows.sort(key=lambda row: row["created_at"], reverse=True)
    window = Page.of(rows, page, size)
    return Page[TechnicalUserSummary](items=[projections.summary(row, viewer(row)) for row in window.items],
                                      page=window.page, size=window.size, total=window.total)


def get_technical_user(*, id: str, company_id: str, **_other: object) -> TechnicalUser:
    row = accounts.find(id)
    return projections.details(row, accounts.viewer_of(row, company_id))


def get_any_technical_user(*, id: str, **_other: object) -> TechnicalUser:
    return projections.details(accounts.find(id), Viewer.OSP)


def list_technical_users(*, company_id: str, page: int = 0, size: int = 20, status: str | list[str] | None = None,
                         origin: str | None = None, wallet_access: str | None = None,
                         **_other: object) -> Page[TechnicalUserSummary]:
    rows = repository.find(visible_to=company_id, statuses=_statuses(status), origin=origin,
                           wallet_access=wallet_access)
    return _page(rows, lambda row: _viewer(row, company_id), page=page, size=size)


def _viewer(row: TechnicalUserRecord, company_id: str) -> Viewer:
    return Viewer.OWNER if row["company_id"] == company_id else Viewer.CO_VIEWER


def list_all_technical_users(*, page: int = 0, size: int = 20, company_id: str | None = None,
                             status: str | list[str] | None = None, origin: str | None = None,
                             wallet_access: str | None = None, disabled: bool | None = None,
                             **_other: object) -> Page[TechnicalUserSummary]:
    rows = repository.find(owner_company_id=company_id, statuses=_statuses(status), origin=origin,
                           wallet_access=wallet_access, disabled=disabled)
    return _page(rows, lambda _row: Viewer.OSP, page=page, size=size)


def check_technical_user(*, id: str, company_id: str | None = None, offer_subscription_id: str | None = None,
                         **_other: object) -> TechnicalUserCheck:
    """9.1: always answers, an unknown ID gives `exists: false`."""
    row = repository.get(id)
    if row is None:
        return TechnicalUserCheck(exists=False, usable_for_connector=False)
    return TechnicalUserCheck(exists=True, belongs_to_company=row["company_id"] == company_id, status=row["status"],
                              origin=row["origin"], wallet_access=row["wallet_access"], disabled=row["disabled"],
                              usable_for_connector=state.usable_for_connector(row, company_id, offer_subscription_id))

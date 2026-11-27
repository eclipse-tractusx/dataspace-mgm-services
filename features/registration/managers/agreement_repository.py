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
"""Repository of the terms (README 5, 6.8): the versions of every agreement in the table `agreement_version`,
seeded with the initial values of the reference catalogue when the table is empty.
"""
from __future__ import annotations

import weakref

from sqlmodel import col, select

from features.registration.managers import application_repository, reference_catalog
from features.registration.models import MODULE
from features.registration.models.tables import AgreementVersionRow, AuditRow
from features.registration.models.value_sets import AgreementScope, AgreementStatus
from portal_common import database

_seeded: weakref.WeakSet = weakref.WeakSet()


def seed() -> None:
    """Take over the initial versions unless the table already holds terms (start, reset, first use)."""
    engine = database.engine(MODULE)
    if engine in _seeded:
        return
    with application_repository.session() as s:
        if s.exec(select(AgreementVersionRow.seq)).first() is None:
            s.add_all(AgreementVersionRow(**x) for x in reference_catalog.initial_agreements())
    _seeded.add(engine)


def reset() -> None:
    """After the tables were emptied: the initial versions again."""
    _seeded.discard(database.engine(MODULE))
    seed()


def versions(status: AgreementStatus | str | None = None) -> list[AgreementVersionRow]:
    """All versions (or those with this status) in the order they were taken over or created."""
    seed()
    query = select(AgreementVersionRow).order_by(col(AgreementVersionRow.seq))
    if status:
        query = query.where(AgreementVersionRow.status == status)
    with application_repository.session() as s:
        return list(s.exec(query))


def required(company_roles: list[str]) -> list[AgreementVersionRow]:
    """Required terms (6.8): active with scope ALL, plus active ones assigned to a selected role."""
    roles = set(company_roles)
    return [a for a in versions(AgreementStatus.ACTIVE)
            if a.scope == AgreementScope.ALL or roles.intersection(a.company_roles)]


def exists(agreement_key: str, version: str) -> bool:
    seed()
    with application_repository.session() as s:
        query = select(AgreementVersionRow.seq).where(AgreementVersionRow.agreement_key == agreement_key,
                                                      AgreementVersionRow.version == version)
        return s.exec(query).first() is not None


def activate(new: AgreementVersionRow, audit: AuditRow) -> None:
    """7.16: the new version becomes the active one, the earlier versions of the agreement inactive."""
    with application_repository.session() as s:
        earlier_versions = select(AgreementVersionRow).where(AgreementVersionRow.agreement_key == new.agreement_key)
        for earlier in s.exec(earlier_versions):
            earlier.status = AgreementStatus.INACTIVE
            s.add(earlier)
        s.add(new)
        s.add(audit)

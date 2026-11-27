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
"""Repository of the company profile (spec C3-M1 README 5) on the feature's own database (F17).

The tables are the SQLModel classes of `models/tables.py`; this module is the only code that opens
`database.session(MODULE)`. The database is chosen at call time by `portal_common.database`:
`COMPANY_PROFILE_DATABASE_URL`, then `C3_M1_DATABASE_URL`, then `DATABASE_URL` (README 4); without one, a
private in-memory SQLite database, so tests and `demo.py` run without a server.

Functions take and return plain dicts with the snake_case column names of README 5 (copies: changing a
returned dict changes nothing). They keep the invariants the spec puts on the database: the value sets, one
identifier per type, one `OPEN` change request per company, a BPN unique among companies that are not
`REJECTED`. A broken invariant raises `ValueError`. Nothing here is FastAPI, HTTP or events.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import re
import threading
import unicodedata
import uuid
import zlib
from collections.abc import Iterable, Iterator
from enum import StrEnum

from sqlalchemy import exists, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, delete, select

from features.company_profile.models import MODULE
from features.company_profile.models.tables import (
    COMPANY_FIELDS,
    AuditRow,
    ChangeRequestRow,
    CompanyRow,
    ConsentRow,
    DocumentRow,
    IdentifierRow,
    RoleRow,
    UsedAttestationRow,
)
from features.company_profile.models.value_sets import (
    ChangeRequestStatus,
    CompanyStatus,
    ConsentSourceKind,
    ConsentStatus,
    CoreDataSource,
    DeactivationReason,
    IdentifierSource,
    IdentifierType,
    MediaType,
    RoleSourceKind,
    RoleStatus,
    values,
)
from portal_common import database

__all__ = ["COMPANY_FIELDS", "value_normalized"]

NORMALISE_STRIP = re.compile(r"[\s.\-/]")
_HIDDEN = {"seq"}


def value_normalized(value: object) -> str:
    """Upper case without spaces, `.`, `-` and `/` (5, 6.4): what the duplicate search compares."""
    return NORMALISE_STRIP.sub("", unicodedata.normalize("NFKC", str(value))).upper()


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _dump(row: SQLModel) -> dict:
    return row.model_dump(exclude=_HIDDEN)


def _dump_or_none(row: SQLModel | None) -> dict | None:
    return _dump(row) if row is not None else None


def _check_enum(value: object, allowed: type[StrEnum], field: str) -> None:
    if value is not None and value not in values(allowed):
        raise ValueError(f"{field}: {value!r} is not one of {', '.join(values(allowed))}")


def _flush(session: Session, conflict: str) -> None:
    """Write now, so a unique index of README 5 answers as `ValueError` instead of at commit."""
    try:
        session.flush()
    except IntegrityError as error:
        raise ValueError(conflict) from error


@contextlib.contextmanager
def _session() -> Iterator[Session]:
    with database.session(MODULE) as session:
        yield session


def reset() -> None:
    """Empty every table (start and tests)."""
    database.reset_tables(MODULE)


def create_tables() -> None:
    """Create the tables that do not exist yet (start of the runtime)."""
    database.create_tables(MODULE)


# ----------------------------------------------------------------------------- lock (README 6.9)
_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


@contextlib.contextmanager
def lock(company_id: str | None = None) -> Iterator[str | None]:
    """The lock of README 6.9: one changing caller per company for the duration of the block.

    In the process an `RLock` per company; on PostgreSQL also a session advisory lock, so replicas of the
    runtime exclude each other. Yields the `companyId` and never looks the company up.
    """
    if not company_id:
        yield company_id
        return
    with _locks_guard:
        local = _locks.setdefault(company_id, threading.RLock())
    with local, _advisory_lock(company_id):
        yield company_id


@contextlib.contextmanager
def _advisory_lock(company_id: str) -> Iterator[None]:
    engine = database.engine(MODULE)
    if engine.dialect.name != "postgresql":
        yield
        return
    key = zlib.crc32(company_id.encode())
    with engine.connect() as connection:
        connection.execute(select(func.pg_advisory_lock(key)))
        connection.commit()
        try:
            yield
        finally:
            connection.execute(select(func.pg_advisory_unlock(key)))
            connection.commit()


# ------------------------------------------------------------------------------ company (README 5)
def _company(session: Session, company_id: str | None) -> CompanyRow | None:
    return session.get(CompanyRow, company_id) if company_id else None


def _known(session: Session, company_id: str) -> CompanyRow:
    row = _company(session, company_id)
    if row is None:
        raise ValueError(f"unknown company: {company_id}")
    return row


def _checked_bpn(session: Session, bpn: object, *, company_id: str, status: str) -> str | None:
    """Upper case and unique among the companies whose status is not `REJECTED` (README 5)."""
    if bpn in (None, ""):
        return None
    if not isinstance(bpn, str):
        raise ValueError("bpn: not a string")
    bpn = bpn.strip().upper()
    if status != CompanyStatus.REJECTED:
        other = session.exec(select(CompanyRow.id).where(
            CompanyRow.bpn == bpn, CompanyRow.id != company_id,
            CompanyRow.status != CompanyStatus.REJECTED)).first()
        if other is not None:
            raise ValueError(f"bpn: {bpn} belongs to company {other}")
    return bpn


def _check_company(status: object, core_data_source: object, reason: object) -> None:
    _check_enum(status, CompanyStatus, "status")
    _check_enum(core_data_source, CoreDataSource, "core_data_source")
    _check_enum(reason, DeactivationReason, "deactivation_reason")
    if reason and status != CompanyStatus.INACTIVE:
        raise ValueError("deactivation_reason: only with status INACTIVE")


def _unknown_fields(fields: Iterable[str]) -> None:
    unknown = set(fields) - set(COMPANY_FIELDS)
    if unknown:
        raise ValueError(f"unknown company fields: {', '.join(sorted(unknown))}")


def get_company(company_id: str | None) -> dict | None:
    with _session() as session:
        return _dump_or_none(_company(session, company_id))


def create_company(row: dict) -> dict:
    _unknown_fields(row)
    if not row.get("id"):
        raise ValueError("id: required")
    values_ = {key: value for key, value in row.items() if value is not None}
    status = values_.setdefault("status", CompanyStatus.REQUESTED)
    values_.setdefault("core_data_source", CoreDataSource.MANUAL)
    _check_company(status, values_["core_data_source"], values_.get("deactivation_reason"))
    for required in ("name", "street", "city", "country_code"):
        if not values_.get(required):
            raise ValueError(f"{required}: required")
    now = _now()
    values_.setdefault("created_at", now)
    values_.setdefault("changed_at", now)
    with _session() as session:
        if _company(session, row["id"]) is not None:
            raise ValueError(f"id: company {row['id']} exists")
        values_["bpn"] = _checked_bpn(session, row.get("bpn"), company_id=row["id"], status=status)
        created = CompanyRow(**values_)
        session.add(created)
        _flush(session, "bpn: belongs to another company with a status other than REJECTED")
        return _dump(created)


def update_company(company_id: str, **fields) -> dict | None:
    _unknown_fields(fields)
    fields.pop("id", None)
    with _session() as session:
        row = _company(session, company_id)
        if row is None:
            return None
        status = fields.get("status", row.status)
        _check_company(status, fields.get("core_data_source", row.core_data_source),
                       fields.get("deactivation_reason", row.deactivation_reason))
        if "bpn" in fields:
            fields["bpn"] = _checked_bpn(session, fields["bpn"], company_id=company_id, status=status)
        for key, value in fields.items():
            setattr(row, key, value)
        row.changed_at = _now()
        session.add(row)
        _flush(session, "bpn: belongs to another company with a status other than REJECTED")
        return _dump(row)


def _statuses(status: str | Iterable[str] | None, allowed: type[StrEnum]) -> list[str]:
    statuses = [status] if isinstance(status, str) else list(status or [])
    for value in statuses:
        _check_enum(value, allowed, "status")
    return statuses


def _collapsed(text: str | None) -> str:
    return " ".join((text or "").split()).casefold()


def find_companies(*, status: str | Iterable[str] | None = None, name: str | None = None, bpn: str | None = None,
                   has_bpn: bool | None = None, company_role: str | None = None,
                   core_data_source: str | None = None, page: int = 0, size: int = 20) -> tuple[list[dict], int]:
    """7.10: filters, newest first, paged. `company_role` matches active roles only.

    The name matches case- and space-insensitively as a substring, which SQL cannot express portably: with a
    name the other filters run in the database and the name and the page in Python."""
    statuses = _statuses(status, CompanyStatus)
    _check_enum(core_data_source, CoreDataSource, "core_data_source")
    query = select(CompanyRow)
    if statuses:
        query = query.where(col(CompanyRow.status).in_(statuses))
    if bpn:
        query = query.where(func.upper(CompanyRow.bpn) == bpn.upper())
    if has_bpn is not None:
        query = query.where(col(CompanyRow.bpn).isnot(None) if has_bpn else col(CompanyRow.bpn).is_(None))
    if core_data_source:
        query = query.where(CompanyRow.core_data_source == core_data_source)
    if company_role:
        query = query.where(exists().where(RoleRow.company_id == CompanyRow.id,
                                           RoleRow.company_role == company_role,
                                           RoleRow.status == RoleStatus.ACTIVE))
    query = query.order_by(col(CompanyRow.created_at).desc(), col(CompanyRow.id).desc())
    start = max(page, 0) * size
    with _session() as session:
        if name:
            wanted = _collapsed(name)
            rows = [row for row in session.exec(query) if wanted in _collapsed(row.name)]
            return [_dump(row) for row in rows[start:start + size]], len(rows)
        total = session.exec(select(func.count()).select_from(query.subquery())).one()
        rows = session.exec(query.offset(start).limit(size)).all()
        return [_dump(row) for row in rows], total


# ------------------------------------------------------------- company_identifier (README 5, 6.4)
def list_identifiers(company_id: str) -> list[dict]:
    with _session() as session:
        rows = session.exec(select(IdentifierRow).where(IdentifierRow.company_id == company_id)
                            .order_by(col(IdentifierRow.seq))).all()
        return [_dump(row) for row in rows]


def identifiers_by_company(company_ids: list[str]) -> dict[str, list[dict]]:
    """The identifiers of many companies in one query: companyId -> identifiers in their order."""
    found: dict[str, list[dict]] = {}
    if not company_ids:
        return found
    with _session() as session:
        rows = session.exec(select(IdentifierRow).where(col(IdentifierRow.company_id).in_(company_ids))
                            .order_by(col(IdentifierRow.seq))).all()
        for row in rows:
            found.setdefault(row.company_id, []).append(_dump(row))
    return found


def _identifier_rows(company_id: str, identifiers: list[dict]) -> list[IdentifierRow]:
    rows: dict[str, IdentifierRow] = {}
    now = _now()
    for entry in identifiers:
        kind = entry.get("type")
        _check_enum(kind, IdentifierType, "type")
        if not kind:
            raise ValueError("type: required")
        if kind in rows:
            raise ValueError(f"type: {kind} given twice")
        source = entry.get("source") or IdentifierSource.DECLARED
        _check_enum(source, IdentifierSource, "source")
        value = entry.get("value")
        if not isinstance(value, str) or not value:
            raise ValueError("value: required")
        rows[kind] = IdentifierRow(company_id=company_id, type=kind, value=value,
                                   value_normalized=value_normalized(value), source=source,
                                   created_at=now, changed_at=now)
    return list(rows.values())


def set_identifiers(company_id: str, identifiers: list[dict]) -> list[dict]:
    """Replace the identifiers; at most one per type (unique `(company_id, type)`), in the given order."""
    with _session() as session:
        _known(session, company_id)
        rows = _identifier_rows(company_id, identifiers)
        session.exec(delete(IdentifierRow).where(col(IdentifierRow.company_id) == company_id))
        session.add_all(rows)
    return list_identifiers(company_id)


# -------------------------------------------------------- company_role_assignment (README 5, 6.5)
def _role(session: Session, company_id: str, company_role: str) -> RoleRow | None:
    return session.exec(select(RoleRow).where(RoleRow.company_id == company_id,
                                              RoleRow.company_role == company_role)).first()


def get_role(company_id: str, company_role: str) -> dict | None:
    with _session() as session:
        return _dump_or_none(_role(session, company_id, company_role))


def role_status(company_id: str, company_role: str) -> str:
    """`REQUESTED`, `ACTIVE`, `INACTIVE`, or `NONE` if the company never had the role."""
    row = get_role(company_id, company_role)
    return row["status"] if row else "NONE"


def list_roles(company_id: str | None) -> dict[str, str]:
    """Role -> status of every role the company has or had, in the order the roles were first added."""
    return roles_by_company([company_id]).get(company_id, {}) if company_id else {}


def roles_by_company(company_ids: list[str]) -> dict[str, dict[str, str]]:
    """The roles of many companies in one query: companyId -> role -> status, in the order of `list_roles`."""
    found: dict[str, dict[str, str]] = {}
    if not company_ids:
        return found
    with _session() as session:
        rows = session.exec(select(RoleRow.company_id, RoleRow.company_role, RoleRow.status)
                            .where(col(RoleRow.company_id).in_(company_ids)).order_by(col(RoleRow.seq))).all()
    for company_id, role, status in rows:
        found.setdefault(company_id, {})[role] = status
    return found


def add_role(company_id: str, company_role: str, *, status: str = RoleStatus.ACTIVE,
             source_kind: str = RoleSourceKind.COMPANY, source_ref: str | None = None) -> dict:
    if not company_role:
        raise ValueError("company_role: required")
    _check_enum(status, RoleStatus, "status")
    _check_enum(source_kind, RoleSourceKind, "source_kind")
    now = _now()
    with _session() as session:
        _known(session, company_id)
        row = _role(session, company_id, company_role) or RoleRow(company_id=company_id,
                                                                  company_role=company_role,
                                                                  status=status, source_kind=source_kind,
                                                                  changed_at=now)
        row.status, row.source_kind, row.source_ref, row.changed_at = status, source_kind, source_ref, now
        if status == RoleStatus.ACTIVE:
            row.activated_at = row.activated_at or now
            row.deactivated_at = None
        if status == RoleStatus.INACTIVE:
            row.deactivated_at = now
        session.add(row)
        session.flush()
        return _dump(row)


def remove_role(company_id: str, company_role: str) -> dict | None:
    """Removal keeps the row: status `INACTIVE` (README 5)."""
    with _session() as session:
        row = _role(session, company_id, company_role)
        if row is None:
            return None
        row.status = RoleStatus.INACTIVE
        row.changed_at = row.deactivated_at = _now()
        session.add(row)
        return _dump(row)


# ------------------------------------------------------------------- consent (README 5, 6.5)
def get_consent(company_id: str, agreement_key: str) -> dict | None:
    with _session() as session:
        return _dump_or_none(session.get(ConsentRow, (company_id, agreement_key)))


def list_consents(company_id: str) -> list[dict]:
    with _session() as session:
        rows = session.exec(select(ConsentRow).where(ConsentRow.company_id == company_id)
                            .order_by(col(ConsentRow.agreement_key))).all()
        return [_dump(row) for row in rows]


def set_consent(company_id: str, agreement_key: str, *, version: str | None = None,
                status: str = ConsentStatus.ACTIVE, source_kind: str = ConsentSourceKind.COMPANY,
                source_ref: str | None = None, consented_by: str | None = None,
                consented_at: str | None = None) -> dict:
    """One row per company and terms, with the latest state (README 5); no `version` keeps the stored one."""
    if not agreement_key:
        raise ValueError("agreement_key: required")
    _check_enum(status, ConsentStatus, "status")
    _check_enum(source_kind, ConsentSourceKind, "source_kind")
    with _session() as session:
        _known(session, company_id)
        row = session.get(ConsentRow, (company_id, agreement_key)) or ConsentRow(
            company_id=company_id, agreement_key=agreement_key, status=status, source_kind=source_kind,
            changed_at=_now())
        row.status, row.source_kind, row.source_ref = status, source_kind, source_ref
        row.consented_by, row.consented_at, row.changed_at = consented_by, consented_at, _now()
        if version is not None:
            row.agreement_version = version
        session.add(row)
        return _dump(row)


# -------------------------------------------------------------- change_request (README 5, 7.4)
def _change_request(session: Session, change_request_id: str | None) -> ChangeRequestRow | None:
    if not change_request_id:
        return None
    return session.exec(select(ChangeRequestRow).where(ChangeRequestRow.id == change_request_id)).first()


def get_change_request(change_request_id: str | None) -> dict | None:
    with _session() as session:
        return _dump_or_none(_change_request(session, change_request_id))


def create_change_request(row: dict) -> dict:
    """At most one change request with status `OPEN` per company (partial unique index)."""
    company_id: str = row.get("company_id") or ""
    status = row.get("status") or ChangeRequestStatus.OPEN
    _check_enum(status, ChangeRequestStatus, "status")
    conflict = f"company {company_id} already has an open change request"
    with _session() as session:
        _known(session, company_id)
        if status == ChangeRequestStatus.OPEN and _open_change_request(session, company_id) is not None:
            raise ValueError(conflict)
        created = ChangeRequestRow(
            id=row.get("id") or str(uuid.uuid4()), company_id=company_id, status=status,
            changes=row.get("changes") or {}, comment=row.get("comment"), requested_by=row.get("requested_by"),
            decided_by=row.get("decided_by"), decision_reason=row.get("decision_reason"),
            created_at=row.get("created_at") or _now(), closed_at=row.get("closed_at"))
        session.add(created)
        _flush(session, conflict)
        return _dump(created)


def _open_change_request(session: Session, company_id: str) -> ChangeRequestRow | None:
    return session.exec(select(ChangeRequestRow).where(
        ChangeRequestRow.company_id == company_id, ChangeRequestRow.status == ChangeRequestStatus.OPEN)).first()


def open_change_request(company_id: str) -> dict | None:
    with _session() as session:
        return _dump_or_none(_open_change_request(session, company_id))


def list_change_requests(*, company_id: str | None = None, status: str | Iterable[str] | None = None,
                         page: int = 0, size: int = 20,
                         newest_first: bool = False) -> tuple[list[dict], int]:
    """7.5 (newest first) and 7.14 (oldest first, the default), paged."""
    statuses = _statuses(status, ChangeRequestStatus)
    query = select(ChangeRequestRow)
    if company_id is not None:
        query = query.where(ChangeRequestRow.company_id == company_id)
    if statuses:
        query = query.where(col(ChangeRequestRow.status).in_(statuses))
    order = (col(ChangeRequestRow.created_at), col(ChangeRequestRow.seq))
    query = query.order_by(*(column.desc() for column in order) if newest_first else order)
    with _session() as session:
        total = session.exec(select(func.count()).select_from(query.subquery())).one()
        rows = session.exec(query.offset(max(page, 0) * size).limit(size)).all()
        return [_dump(row) for row in rows], total


def _close(change_request_id: str, status: str, **fields) -> dict | None:
    with _session() as session:
        row = _change_request(session, change_request_id)
        if row is None:
            return None
        if row.status != ChangeRequestStatus.OPEN:
            raise ValueError(f"status: {row.status} is not OPEN")
        row.status = status
        for key, value in fields.items():
            setattr(row, key, value)
        session.add(row)
        return _dump(row)


_DECISIONS = (ChangeRequestStatus.APPROVED.value, ChangeRequestStatus.DECLINED.value)


def decide_change_request(change_request_id: str, status: str, *, decided_by: str | None = None,
                          decision_reason: str | None = None, closed_at: str | None = None) -> dict | None:
    """Only an `OPEN` request can be decided; `DECLINED` needs the justification (7.18)."""
    if status not in _DECISIONS:
        raise ValueError(f"status: {status!r} is not one of {', '.join(_DECISIONS)}")
    if status == ChangeRequestStatus.DECLINED and not decision_reason:
        raise ValueError("decision_reason: required with DECLINED")
    return _close(change_request_id, status, decided_by=decided_by, decision_reason=decision_reason,
                  closed_at=closed_at or _now())


def withdraw_change_request(change_request_id: str, *, closed_at: str | None = None) -> dict | None:
    return _close(change_request_id, ChangeRequestStatus.WITHDRAWN, closed_at=closed_at or _now())


# ----------------------------------------------------- change_request_document (README 5, 7.4)
def add_document(change_request_id: str, *, file_name: str, media_type: str, content: bytes = b"",
                 size_bytes: int | None = None, sha256: str | None = None) -> dict:
    _check_enum(media_type, MediaType, "media_type")
    with _session() as session:
        if _change_request(session, change_request_id) is None:
            raise ValueError(f"unknown change request: {change_request_id}")
        row = DocumentRow(id=str(uuid.uuid4()), change_request_id=change_request_id, file_name=file_name,
                          media_type=media_type, size_bytes=len(content) if size_bytes is None else size_bytes,
                          sha256=sha256 or hashlib.sha256(content).hexdigest(), content=content,
                          created_at=_now())
        session.add(row)
        session.flush()
        return _dump(row)


def get_document(document_id: str | None) -> dict | None:
    if not document_id:
        return None
    with _session() as session:
        return _dump_or_none(session.exec(select(DocumentRow).where(DocumentRow.id == document_id)).first())


def list_documents(change_request_id: str) -> list[dict]:
    with _session() as session:
        rows = session.exec(select(DocumentRow).where(DocumentRow.change_request_id == change_request_id)
                            .order_by(col(DocumentRow.seq))).all()
        return [_dump(row) for row in rows]


# ------------------------------------------------------------- used_attestation (README 5, 6.7)
def add_if_unused(jti: str, company_id: str) -> bool:
    """`True` if the `jti` was free and is now used, `False` if it was used already."""
    if not jti:
        raise ValueError("jti: required")
    with _session() as session:
        _known(session, company_id)
        if session.get(UsedAttestationRow, jti) is not None:
            return False
        session.add(UsedAttestationRow(jti=jti, company_id=company_id, used_at=_now()))
        return True


def is_used(jti: str) -> bool:
    with _session() as session:
        return session.get(UsedAttestationRow, jti) is not None


# -------------------------------------------------------------------- audit_log (README 5, 4.3)
def audit(company_id: str | None, sub: str | None, operation: str, object_id: str | None = None,
          details: dict | None = None) -> dict:
    """Every changing operation, every step and every read of a document (FRAMEWORK 4.3)."""
    with _session() as session:
        row = AuditRow(id=str(uuid.uuid4()), occurred_at=_now(), sub=sub or "", company_id=company_id,
                       operation=operation, object_id=object_id, details=details or {})
        session.add(row)
        session.flush()
        return _dump(row)


def list_audit(company_id: str | None = None) -> list[dict]:
    query = select(AuditRow).order_by(col(AuditRow.seq))
    if company_id is not None:
        query = query.where(AuditRow.company_id == company_id)
    with _session() as session:
        return [_dump(row) for row in session.exec(query).all()]

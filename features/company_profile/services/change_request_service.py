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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""Change requests of core data: raised by the company (7.4 to 7.6), reviewed by OSP staff (7.14 to 7.18).
"""
from __future__ import annotations

from features.company_profile.managers import company_repository, config
from features.company_profile.models.change_request import (
    ChangeRequest,
    ChangeRequestCompany,
    ChangeRequestDetail,
    DocumentContent,
    DocumentInfo,
    ReviewedChangeRequest,
)
from features.company_profile.services import company_validation
from features.company_profile.services.company_changes import (
    changed_fields,
    changes_differs,
    differs_field,
    identifier_core_changed,
    validate_merge,
    wallet_identifier_conflict,
)
from features.company_profile.services.company_views import address_view, get_company, identifiers_view
from features.company_profile.services.shared import MODULE, utc_now
from portal_common import events
from portal_common.models import Page
from portal_common.problems import Problem


# ------------------------------------------------------------ change requests (7.4 - 7.6, 7.14 - 7.18)
def _fields(row: dict) -> dict:
    """The row with its documents (without their content)."""
    return row | {"documents": [DocumentInfo.model_validate(document)
                                for document in company_repository.list_documents(row["id"])]}


def _change_request_view(row: dict) -> ChangeRequest:
    """`ChangeRequest` as the company sees it (7.5: without `companyName` and `decidedBy`)."""
    return ChangeRequest.model_validate(_fields(row))


def _reviewed_view(row: dict, company: dict | None = None) -> ReviewedChangeRequest:
    """`ChangeRequest` as OSP staff see it, with `companyName` and `decidedBy`."""
    return ReviewedChangeRequest.model_validate(_fields(row) | {"company_name": (company or {}).get("name")})


def create_change_request(companyId: str, data: dict,
                          documents: list[tuple[str, bytes, str | None]],
                          sub: str | None = None) -> ChangeRequest:
    """7.4: a change request with supporting documents."""
    if not config.change_requests_enabled():
        raise Problem(MODULE, 409, "change-requests-disabled")
    with company_repository.lock(companyId):
        row = get_company(companyId)
        if row["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        if company_repository.open_change_request(companyId):
            raise Problem(MODULE, 409, "change-request-open")

        changes = {key: value for key, value in data.items() if key in ("name", "address", "identifiers")}
        identifiers = changes.get("identifiers")
        wallet = [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
                  for entry in company_repository.list_identifiers(companyId) if entry["source"] == "BUSINESS_WALLET"]
        errors = company_validation.validate_change_request(data, row["country_code"])
        if identifiers is not None:
            if not identifiers and wallet:
                # "afterwards at least one identifier" counts the wallet identifiers that stay
                errors = [error for error in errors
                          if not (error["field"] == "identifiers" and error["reason"] == "missing")]
            errors += wallet_identifier_conflict(row, identifiers)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)
        core_changed = any(differs_field(row, key, value)
                           for key, value in changes.items() if key != "identifiers")
        if identifiers is not None and identifier_core_changed(row, identifiers):
            core_changed = True
        if core_changed and row["core_data_source"] == "EBW":
            raise Problem(MODULE, 409, "attestation-required")
        if not changes_differs(row, changes):
            raise Problem(MODULE, 400, "validation",
                          errors=[{"field": "changes", "reason": "no change"}])

        errors = []
        if not 1 <= len(documents) <= config.change_request_max_documents():
            errors.append({"field": "documents",
                           "reason": f"1 to {config.change_request_max_documents()} documents"})
        for file_name, content, stated in documents:
            errors += company_validation.validate_document(file_name, content, stated_media_type=stated,
                                                   max_bytes=config.change_request_max_document_bytes())
        if errors:
            raise Problem(MODULE, 400, "document-invalid", errors=errors)

        created = company_repository.create_change_request({
            "company_id": companyId, "changes": changes, "comment": data.get("comment"),
            "requested_by": sub, "status": "OPEN"})
        for file_name, content, stated in documents:
            company_repository.add_document(created["id"], file_name=file_name,
                               media_type=company_validation.detect_media_type(content) or stated or "",
                               content=content)
        company_repository.audit(companyId, sub, "createChangeRequest", created["id"],
                    {"changedFields": sorted(changes)})
        events.publish(MODULE, "CompanyChangeRequestSubmitted",
                       {"companyId": companyId, "changeRequestId": created["id"]})
    return _change_request_view(created)


def list_own_change_requests(companyId: str, page: int = 0, size: int = 20) -> Page[ChangeRequest]:
    """7.5: own change requests, newest first, without `decidedBy`."""
    get_company(companyId)
    items, total = company_repository.list_change_requests(company_id=companyId, page=page, size=size,
                                              newest_first=True)
    return Page[ChangeRequest](items=[_change_request_view(item) for item in items], page=page, size=size,
                               total=total)


def _own_change_request(companyId: str, changeRequestId: str) -> dict:
    row = company_repository.get_change_request(changeRequestId)
    if row is None or row["company_id"] != companyId:
        raise Problem(MODULE, 404, "not-found")
    return row


def withdraw_change_request(companyId: str, changeRequestId: str, sub: str | None = None) -> ChangeRequest:
    """7.6"""
    with company_repository.lock(companyId):
        row = _own_change_request(companyId, changeRequestId)
        if row["status"] == "WITHDRAWN":
            return _change_request_view(row)
        if row["status"] != "OPEN":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        closed = company_repository.withdraw_change_request(changeRequestId)
        company_repository.audit(companyId, sub, "withdrawChangeRequest", changeRequestId)
        events.publish(MODULE, "CompanyChangeRequestClosed",
                       {"companyId": companyId, "changeRequestId": changeRequestId,
                        "outcome": "WITHDRAWN"})
    return _change_request_view(closed)


# ----------------------------------------------------------------------- review by OSP staff (7.14 - 7.18)
def _reviewed(changeRequestId: str) -> dict:
    row = company_repository.get_change_request(changeRequestId)
    if row is None:
        raise Problem(MODULE, 404, "not-found")
    return row


def list_change_requests(*, status: list[str] | str | None = None,
                         companyId: str | None = None, page: int | str = 0,
                         size: int | str = 20) -> Page[ReviewedChangeRequest]:
    """7.14: all change requests, oldest first."""
    try:
        items, total = company_repository.list_change_requests(status=status, company_id=companyId,
                                                  page=int(page or 0), size=int(size or 20))
    except ValueError as error:
        raise Problem(MODULE, 400, "validation", errors=[{"field": "filter", "reason": str(error)}]) from None
    companies = {company_id: company_repository.get_company(company_id)
                 for company_id in {item["company_id"] for item in items}}
    return Page[ReviewedChangeRequest](items=[_reviewed_view(item, companies[item["company_id"]]) for item in items],
                                       page=int(page or 0), size=int(size or 20), total=total)


def get_change_request(changeRequestId: str) -> ChangeRequestDetail:
    """7.15: the request with the current state of the company."""
    row = _reviewed(changeRequestId)
    company = company_repository.get_company(row["company_id"]) or {}
    current = ChangeRequestCompany.model_validate(company | {"address": address_view(company),
                                                             "identifiers": identifiers_view(company)})
    return ChangeRequestDetail.model_validate(_fields(row) | {"company_name": company.get("name"),
                                                              "company": current})


def get_change_request_document(changeRequestId: str, documentId: str,
                                sub: str | None = None) -> DocumentContent:
    """7.16: content, media type and file name; the read is audited."""
    request = _reviewed(changeRequestId)
    document = company_repository.get_document(documentId)
    if document is None or document["change_request_id"] != changeRequestId:
        raise Problem(MODULE, 404, "not-found")
    company_repository.audit(request["company_id"], sub, "getChangeRequestDocument", documentId)
    return DocumentContent.model_validate(document)


def _apply_changes(companyId: str, row: dict, changes: dict) -> tuple[list[str], bool]:
    """Apply the request and return the changed field names and whether core data changed (7.17)."""
    fields = {key: value for key, value in changes.items() if key in ("name", "address")}
    identifiers = changes.get("identifiers")
    stored = company_repository.list_identifiers(companyId)
    wallet = [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
              for entry in stored if entry["source"] == "BUSINESS_WALLET"]
    merged_identifiers = (list(identifiers) + wallet) if identifiers is not None else\
        [{"type": entry["type"], "value": entry["value"], "source": entry["source"]} for entry in stored]
    errors = company_validation.validate_company(validate_merge(row, fields), partial=False)
    errors += company_validation.validate_identifiers(merged_identifiers, row["country_code"])
    if identifiers is not None:
        errors += wallet_identifier_conflict(row, identifiers)
    if errors:
        raise Problem(MODULE, 400, "validation", errors=errors)

    core_changed = any(differs_field(row, key, value) for key, value in fields.items())
    if identifiers is not None and identifier_core_changed(row, identifiers):
        core_changed = True
    if core_changed and row["core_data_source"] == "EBW":
        raise Problem(MODULE, 409, "attestation-required")
    changed = changed_fields(row, fields, identifiers)
    updates = company_validation.flat_fields(fields)
    if core_changed:
        updates |= {"core_data_source": "MANUAL", "core_data_verified_at": utc_now()}
    if updates:
        company_repository.update_company(companyId, **updates)
    if identifiers is not None:
        company_repository.set_identifiers(companyId, merged_identifiers)
    return changed, core_changed


def approve_change_request(changeRequestId: str, body: dict | None = None,
                           sub: str | None = None) -> ReviewedChangeRequest:
    """7.17"""
    with company_repository.lock((company_repository.get_change_request(changeRequestId) or {}).get("company_id")):
        row = _reviewed(changeRequestId)
        if row["status"] == "APPROVED":
            return _reviewed_view(row)
        if row["status"] != "OPEN":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        if row["requested_by"] and row["requested_by"] == sub:
            raise Problem(MODULE, 409, "same-person")
        company = get_company(row["company_id"])
        if company["status"] != "ACTIVE":
            raise Problem(MODULE, 409, "invalid-state", detail=company["status"])

        changed, core_changed = _apply_changes(row["company_id"], company, row["changes"])
        decided = company_repository.decide_change_request(changeRequestId, "APPROVED", decided_by=sub,
                                              decision_reason=None)
        company_repository.audit(row["company_id"], sub, "approveChangeRequest", changeRequestId,
                    {"changedFields": changed, "comment": (body or {}).get("comment")})
        if changed:
            events.publish(MODULE, "CompanyDataChanged",
                           {"companyId": row["company_id"], "changedFields": changed,
                            "coreDataChanged": core_changed,
                            "coreDataSource": "MANUAL" if core_changed
                            else company["core_data_source"]})
        events.publish(MODULE, "CompanyChangeRequestClosed",
                       {"companyId": row["company_id"], "changeRequestId": changeRequestId,
                        "outcome": "APPROVED"})
    return _reviewed_view(decided)


def decline_change_request(changeRequestId: str, body: dict | None = None,
                           sub: str | None = None) -> ReviewedChangeRequest:
    """7.18"""
    with company_repository.lock((company_repository.get_change_request(changeRequestId) or {}).get("company_id")):
        row = _reviewed(changeRequestId)
        reason = (body or {}).get("reason")
        if row["status"] == "DECLINED":
            return _reviewed_view(row)
        if row["status"] != "OPEN":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"])
        errors = company_validation.validate_decision_reason(reason)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors)
        decided = company_repository.decide_change_request(changeRequestId, "DECLINED", decided_by=sub,
                                              decision_reason=reason)
        company_repository.audit(row["company_id"], sub, "declineChangeRequest", changeRequestId,
                    {"reason": reason})
        events.publish(MODULE, "CompanyChangeRequestClosed",
                       {"companyId": row["company_id"], "changeRequestId": changeRequestId,
                        "outcome": "DECLINED"})
    return _reviewed_view(decided)

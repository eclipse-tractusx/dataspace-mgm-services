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
"""Agreement versions managed by OSP staff (README 7.15, 7.16).
"""
from __future__ import annotations

import datetime as dt
import re

from features.registration.managers import reference_catalog
from features.registration.managers.application_repository import applications_lock, audit_log
from features.registration.services import attestation_verifier
from features.registration.services.application_validation import check_roles
from features.registration.services.shared import MODULE, field_error, paginate, utc_now, validation_problem
from portal_common import events
from portal_common.problems import Problem


# ---------------------------------------------------------------------------- terms (7.15, 7.16)
def list_agreement_versions(agreement_key: str | None, status: str | None, page: int, size: int) -> dict:
    found = [a for a in reference_catalog.versions() if (not agreement_key or a["agreementKey"] == agreement_key)
             and (not status or a["status"] == status)]
    found.sort(key=lambda a: a["createdAt"], reverse=True)
    found.sort(key=lambda a: a["agreementKey"])
    return paginate(found, page, size)


def _check_agreement(body: dict) -> list[dict]:
    errors: list[dict] = []
    if not (isinstance(body.get("agreementKey"), str) and re.fullmatch(r"[a-z0-9-]{1,64}", body["agreementKey"])):
        errors.append(field_error("agreementKey", "lower case letters, digits and hyphens, at most 64"))
    if not (isinstance(body.get("version"), str) and 1 <= len(body["version"]) <= 20):
        errors.append(field_error("version", "1 to 20 characters"))
    if body.get("party") not in ("OSP", "DATASPACE"):
        errors.append(field_error("party", "OSP or DATASPACE"))
    scope, company_roles = body.get("scope"), body.get("companyRoles")
    if scope not in ("ALL", "COMPANY_ROLE"):
        errors.append(field_error("scope", "ALL or COMPANY_ROLE"))
    if scope == "COMPANY_ROLE":
        check_roles(company_roles, errors)
        if isinstance(company_roles, list):
            errors += [field_error("companyRoles", f"not selectable: {r}") for r in company_roles if not reference_catalog.selectable(r)]
    elif company_roles:
        errors.append(field_error("companyRoles", "only for scope COMPANY_ROLE"))
    title = body.get("title")
    if not (isinstance(title, dict) and all(isinstance(title.get(k), str) and 1 <= len(title[k]) <= 200 for k in ("de", "en"))):
        errors.append(field_error("title", "de and en, 1 to 200 characters"))
    urls = body.get("documentUrls")
    if not (isinstance(urls, dict) and urls and set(urls) <= {"de", "en"}
            and all(isinstance(u, str) and u.startswith("https://") for u in urls.values())):
        errors.append(field_error("documentUrls", "de or en, at least one, HTTPS"))
    if not isinstance(body.get("reconsentRequired"), bool):
        errors.append(field_error("reconsentRequired", "required"))
    if body.get("reconsentRequired"):
        try:
            due = dt.datetime.fromisoformat(str(body.get("reconsentDueAt")).replace("Z", "+00:00"))
            if due.tzinfo is None or due.timestamp() <= attestation_verifier.now():
                errors.append(field_error("reconsentDueAt", "must be in the future"))
        except ValueError:
            errors.append(field_error("reconsentDueAt", "required with reconsentRequired, date-time"))
    return errors


def create_agreement_version(body: dict, sub: str) -> dict:
    """7.16."""
    errors = _check_agreement(body)
    if errors:
        raise validation_problem(errors)
    with applications_lock:
        versions = reference_catalog.versions()
        if any(a["agreementKey"] == body["agreementKey"] and a["version"] == body["version"] for a in versions):
            raise Problem(MODULE, 409, "conflict", detail="this version of the terms already exists")
        for a in versions:
            if a["agreementKey"] == body["agreementKey"]:
                a["status"] = "INACTIVE"
        new = {"agreementKey": body["agreementKey"], "version": body["version"], "party": body["party"], "scope": body["scope"],
               "companyRoles": list(body.get("companyRoles") or []), "title": body["title"], "documentUrls": body["documentUrls"],
               "status": "ACTIVE", "reconsentRequired": body["reconsentRequired"], "reconsentDueAt": body.get("reconsentDueAt"),
               "createdAt": utc_now(), "createdBy": sub}
        versions.append(new)
        audit_log.append({"at": utc_now(), "sub": sub, "processId": None, "stepRunId": None, "companyId": None,
                          "operation": "createAgreementVersion", "applicationId": None,
                          "objectId": f"{new['agreementKey']}:{new['version']}"})
        events.publish(MODULE, "AgreementVersionActivated", {"agreementKey": new["agreementKey"], "version": new["version"],
                                                             "party": new["party"], "reconsentRequired": new["reconsentRequired"],
                                                             "reconsentDueAt": new["reconsentDueAt"]})
        return new

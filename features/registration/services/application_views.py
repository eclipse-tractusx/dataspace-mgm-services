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
"""The JSON views of an application (`Application`, `ApplicationSummary`, review status 7.4).
"""
from __future__ import annotations

from features.registration.managers import neighbour_client
from portal_common.problems import Problem

SUMMARY_KEYS = ("attestationId", "issuer", "issuedAt", "expiresAt", "verifiedAt", "person", "representation")


# ------------------------------------------------------------------------------------- views
def public(a: dict) -> dict:
    """`Application`: without the JWT and with the extract of the attestation only."""
    out = {k: v for k, v in a.items() if not k.startswith("_")}
    current = a.get("_attestation")
    out["attestation"] = {k: current[k] for k in SUMMARY_KEYS} if current else None
    return out


def summary(a: dict) -> dict:
    """`ApplicationSummary`."""
    return {"id": a["id"], "companyId": a["companyId"], "kind": a["kind"], "existingCompany": a["existingCompany"],
            "verification": a["verification"], "status": a["status"], "legalName": a["companyData"]["legalName"],
            "countryCode": a["companyData"]["address"].get("countryCode"), "companyRoles": a["companyRoles"],
            "createdAt": a["createdAt"], "submittedAt": a.get("submittedAt")}


def _review_status(a: dict) -> str:
    """`reviewStatus` of 7.4."""
    if a["status"] == "CREATED":
        return "NONE"
    try:
        return neighbour_client.review_status(a["id"]) or "NONE"
    except Problem:
        return "UNKNOWN"


def with_review(a: dict) -> dict:
    return public(a) | {"reviewStatus": _review_status(a)}

#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
"""Notifications of the CSP (README 7.2): `OperationCompleted` and `CompanyTransferredAway`."""
from __future__ import annotations

from typing import Any

from features.csp_connection.managers import store
from features.csp_connection.managers.store import Registration
from features.csp_connection.models import errors
from features.csp_connection.models.errors import MODULE
from features.csp_connection.models.schemas import NotificationType, Outcome
from features.csp_connection.services.common import optional_text, require_text
from features.csp_connection.services.registration_state import complete_operation, mark_transferred_away
from portal_common import events
from portal_common.problems import Problem


def receive_csp_notification(body: dict[str, Any]) -> dict[str, str | bool]:
    """Notification from the CSP; a known `notificationId` is acknowledged and not processed again.
    Every notification gets an audit entry, also a duplicate and a rejected one (README 5)."""
    try:
        with store.lock:   # duplicate check, lookup and change in one step (OPEN-QUESTIONS 15)
            return _receive_notification(body)
    except Problem as p:
        kind, bpn = body.get("type"), body.get("bpn")
        store.record_audit(f"notification:{kind if isinstance(kind, str) else 'invalid'}", None,
                           bpn if isinstance(bpn, str) else None, p.status, p.name)
        raise


def _receive_notification(body: dict[str, Any]) -> dict[str, str | bool]:
    notification_id = require_text(body, "notificationId")
    kind = require_text(body, "type")
    if kind == "OperationCompleted":
        kind_type: NotificationType = "OperationCompleted"
    elif kind == "CompanyTransferredAway":
        kind_type = "CompanyTransferredAway"
    else:
        raise errors.validation("type must be OperationCompleted or CompanyTransferredAway")
    bpn = optional_text(body, "bpn")
    if store.has_notification(notification_id):
        store.record_audit(f"notification:{kind_type}", None, bpn, 200, "duplicate")
        return {"notificationId": notification_id, "accepted": True}

    if kind_type == "OperationCompleted":
        row = _operation_completed(body, notification_id, bpn)
    else:
        row = _transferred_away(bpn)

    # Stored only after it was processed, so a failed processing does not swallow the notification.
    store.save(store.Notification(notification_id=notification_id, type=kind_type, bpn=row.bpn))
    store.record_audit(f"notification:{kind_type}", row.company_id, row.bpn, 200)
    return {"notificationId": notification_id, "accepted": True}


def _operation_completed(body: dict[str, Any], notification_id: str, bpn: str | None) -> Registration:
    """`OperationCompleted` (README 7.2): ends the operation of the registration it belongs to."""
    operation_id = require_text(body, "operationId")
    outcome = require_text(body, "outcome")
    if outcome == "SUCCEEDED":
        result: Outcome = "SUCCEEDED"
    elif outcome == "FAILED":
        result = "FAILED"
    else:
        raise errors.validation("outcome must be SUCCEEDED or FAILED")
    reason = optional_text(body, "reason")
    if outcome == "SUCCEEDED" and not bpn:
        raise errors.validation("bpn is required with outcome SUCCEEDED")
    # The operation id identifies the registration; the BPN is the fallback (README 7.2 step 2),
    # but only for a registration that still waits (PENDING): a late notification must not
    # revive a FAILED or TRANSFERRED_AWAY company (README 6.1). An unknown one answers 404 and
    # is not stored, so the CSP can send it again once it is known here (OPEN-QUESTIONS 9).
    row = store.find_by_operation(operation_id) or (
        store.find_by_bpn(bpn, status="PENDING") if bpn else None)
    if row is None:
        # Possibly earlier than the 202 answer of the step: keep it aside, the step applies it
        # when it stores the operation id (OPEN-QUESTIONS 15). The answer stays 404 (README 7.2).
        store.keep_early_completion(store.EarlyCompletion(notification_id=notification_id,
                                                          operation_id=operation_id, outcome=result, bpn=bpn,
                                                          reason=reason))
        raise errors.unknown_company(f"no registration for operation {operation_id}")
    return complete_operation(row.company_id, result, bpn, reason)


def _transferred_away(bpn: str | None) -> Registration:
    """`CompanyTransferredAway` (README 7.2, FRAMEWORK 5.6): the company now lives at another OSP."""
    if not bpn:
        raise errors.validation("bpn is required with CompanyTransferredAway")
    # Prefer the REGISTERED row: after a company came back, an older row with the same BPN can exist.
    row = store.find_by_bpn(bpn, status="REGISTERED") or store.find_by_bpn(bpn)
    if row is None:
        raise errors.unknown_company(f"no registration for BPN {bpn}")
    if row.status != "TRANSFERRED_AWAY":
        mark_transferred_away(row.company_id)
        events.publish(MODULE, "CompanyTransferredAway", {"companyId": row.company_id, "bpn": bpn})
    return row

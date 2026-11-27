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
"""Status changes of a registration at the CSP (README 6.1) and the answer of a registration or transfer
(README 8.1, 8.2). Every change and its event happen under `store.lock`."""
from __future__ import annotations

from typing import Any

from features.csp_connection.managers import csp_client, store
from features.csp_connection.managers.store import Registration
from features.csp_connection.models import errors
from features.csp_connection.models.errors import MODULE
from features.csp_connection.services.common import (
    REASON_OTHER_OSP,
    REASON_REJECTED,
    StepInputJson,
    StepReply,
    step_reply,
)
from portal_common import events


def mark_registered(company_id: str, bpn: str) -> Registration:
    """Status `REGISTERED` with the BPN. The event goes out only on a change (FRAMEWORK 4.4), so a
    repeated step or a repeated callback never starts the next flow step twice. Read, check, change and
    event happen under `store.lock`, so two threads cannot both see a change."""
    with store.lock:
        row = store.registration_row(company_id)
        changed = row.status != "REGISTERED" or row.bpn != bpn
        row.status, row.bpn, row.failure_reason, row.pending_operation_id = "REGISTERED", bpn, None, None
        row.returning = False
        if changed:
            row.registered_at = store.now()
            row.touch()
        store.save(row)
        if changed:
            events.publish(MODULE, "CompanyRegisteredAtCsp", {"companyId": company_id, "bpn": bpn})
        return row


def mark_rejected(company_id: str, reason: str) -> Registration:
    """The CSP rejected a registration or a transfer. A company that tried to come back from
    `TRANSFERRED_AWAY` stays `TRANSFERRED_AWAY`, because it still lives at the other OSP and
    deregister-membership must keep its exception of README 8.5 (README 6.1; OPEN-QUESTIONS 16).
    Any other company turns `FAILED`. The failure event goes out in both cases, only on a change."""
    with store.lock:
        row = store.registration_row(company_id)
        status = "TRANSFERRED_AWAY" if row.status == "TRANSFERRED_AWAY" or row.returning else "FAILED"
        changed = row.status != status or row.failure_reason != reason
        row.status, row.failure_reason, row.pending_operation_id, row.returning = status, reason, None, False
        if changed:
            row.touch()
        store.save(row)
        if changed:
            events.publish(MODULE, "CompanyRegistrationAtCspFailed", {"companyId": company_id, "reason": reason})
        return row


def complete_operation(company_id: str, outcome: str, bpn: str | None, reason: str | None) -> Registration:
    """End of a long-running operation at the CSP (README 7.2 step 3), from a callback or an early
    one. The row afterwards: `REGISTERED` on success, otherwise rejected."""
    if outcome == "SUCCEEDED" and bpn:
        return mark_registered(company_id, bpn)
    return mark_rejected(company_id, reason or REASON_REJECTED)


def mark_transferred_away(company_id: str) -> None:
    """Status `TRANSFERRED_AWAY`. The new home OSP owns the company at the CSP now (FRAMEWORK 5.6), so
    what this module knew about the company's DID, membership and connectors at the CSP is no longer
    true: forget the DID, set the membership `NONE` and mark the connectors `DEREGISTERED`. After a
    return, register-did, register-membership and register-connector then call the CSP again, even
    with unchanged values (README 6.4, 8.5; OPEN-QUESTIONS 14). No event for these resets."""
    with store.lock:
        row = store.registration_row(company_id)
        row.status, row.did, row.membership = "TRANSFERRED_AWAY", None, "NONE"
        # A registration or return still waiting at the CSP is over: forget its operation id, so a
        # late OperationCompleted cannot find the company by it and revive it (README 6.1).
        row.pending_operation_id, row.returning = None, False
        row.touch()
        connectors = store.registered_connectors_of(company_id)
        for con in connectors:
            con.status, con.updated_at = "DEREGISTERED", row.updated_at
        store.save(row, *connectors)


def registration_answer(input: StepInputJson, company_id: str, status: int, answer: object) -> StepReply:
    """Answer of `POST /companies` or `POST /companies/{bpn}/transfer` (README 8.1, 8.2)."""
    body: dict[str, Any] = answer if isinstance(answer, dict) else {}
    if status == 201:
        bpn = body.get("bpn")
        if not isinstance(bpn, str) or not bpn:
            raise errors.upstream_error("the CSP confirmed without a BPN")
        # Precondition of README 8.1: no other REGISTERED company with the same EBWOID or EUID. The
        # module may not store them (README 5), so the check uses the BPN the CSP derives from them
        # (OPEN-QUESTIONS 1). Nothing is changed on this path.
        if (other := store.find_by_bpn(bpn, exclude=company_id, status="REGISTERED")) is not None:
            raise errors.invalid_state(f"BPN {bpn} is already registered for company {other.company_id}")
        mark_registered(company_id, bpn)
        return step_reply(input, {"bpn": bpn})
    if status == 202:
        operation_id = body.get("operationId")
        if not isinstance(operation_id, str) or not operation_id:
            raise errors.upstream_error("the CSP accepted without an operationId")
        return _pending(input, company_id, operation_id)
    # Final answers turn the row FAILED and publish the failure event: 409 = another OSP is the
    # home OSP, any other 4xx = business rejection (OPEN-QUESTIONS 2, 3). A 5xx or no answer
    # leaves the row as it was; raise_for answers retryable and C12 tries the step again.
    if status == 409:
        mark_rejected(company_id, REASON_OTHER_OSP)
        home = body.get("homeOspId")
        raise errors.registered_at_other_osp(home if isinstance(home, str) else None)
    if csp_client.is_business_rejection(status):
        mark_rejected(company_id, REASON_REJECTED)
    csp_client.raise_for(status, answer, ok=())
    raise AssertionError("unreachable")  # raise_for always raises with ok=()


def _pending(input: StepInputJson, company_id: str, operation_id: str) -> StepReply:
    """The CSP accepted (202): `PENDING` with the operation id, or at once the completion that came first.
    Storing PENDING and taking a callback that came first happen under `store.lock`; the callback looks
    up the operation under the same lock, so it is either found here or finds the row (OPEN-QUESTIONS 15).
    Without this the company would wait for ever."""
    with store.lock:
        row = store.registration_row(company_id)
        row.status, row.pending_operation_id, row.failure_reason = "PENDING", operation_id, None
        row.touch()
        store.save(row)
        early = store.pop_early_completion(operation_id)
        if early is None:
            return step_reply(input, state="RUNNING")
        row = complete_operation(company_id, early.outcome, early.bpn, early.reason)
        store.save(store.Notification(notification_id=early.notification_id, type="OperationCompleted", bpn=row.bpn))
        store.record_audit("notification:OperationCompleted", company_id, row.bpn, 200, "applied-late")
    if row.status == "REGISTERED" and early.bpn:
        return step_reply(input, {"bpn": early.bpn})
    raise errors.csp_rejected(f"the CSP rejected the operation ({row.failure_reason})", None)

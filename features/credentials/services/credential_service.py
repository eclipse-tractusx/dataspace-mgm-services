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
"""Business rules of the credentials (spec C4-M1, README 6, 7.3, 7.4, 8).

Talks only to the `CredentialStore` interface (`store()`), never to dicts. Every change of a row
writes `credential_history` (README 6.1); every operation for one company runs inside
`store().transaction(company_id)` (README 6.6). All time reads go through `now()`. The read views
(README 7.1, 7.2, 9.1) are in `credential_views.py`.
"""
from __future__ import annotations

import datetime as dt
import uuid

from features.credentials.managers import config, neighbour_client
from features.credentials.managers.credential_store import CredentialStore as CredentialStore  # for interface
from features.credentials.managers.credential_store import store
from features.credentials.managers.issuer_clients import IssuerRoute
from features.credentials.models import errors
from features.credentials.models.credentials import (
    ConfirmRevocation,
    CredentialDetail,
    CredentialOutcome,
    IssueCredentials,
    IssueResult,
    IssuerReport,
    RevocationResult,
    RevokeCredentials,
)
from features.credentials.models.errors import MODULE, parse
from features.credentials.models.values import CREDENTIAL_ISSUER, CREDENTIAL_KINDS, CredentialType
from features.credentials.services import issuer_routes as routes
from portal_common import events
from portal_common.models import StepResult


def now() -> dt.datetime:
    """The single clock of the module (timezone-aware UTC); tests patch it."""
    return dt.datetime.now(dt.UTC)


def reset() -> None:
    """Empties the store and cancels pending STUB timers."""
    routes.reset()
    store().reset()


def flush_timers() -> None:
    """Fires every pending STUB issuer timer now, through the code path of the HTTP callback (tests)."""
    routes.flush_stub()


# ------------------------------------------------------------------------------------------ helpers
def _truncate(text: str | None, n: int) -> str | None:
    return None if text is None else text[:n]


def _change(row: dict, status: str, note: str | None = None, **fields: object) -> dict:
    """Sets the status of a row and writes the history entry (README 6.1)."""
    t = now()
    row.update(fields)
    row.update(status=status, changed_at=t)
    store().put_credential(row)
    store().append_history({"id": str(uuid.uuid4()), "credential_id": row["id"], "occurred_at": t,
                            "status": status, "attempt": row["attempt"], "note": _truncate(note, 1000)})
    return row


def _put_run(cid: str, types: list[CredentialType], status: str, process_id: str | None = None,
             step_run_id: str | None = None, started_at: dt.datetime | None = None,
             finished_at: dt.datetime | None = None) -> dict:
    run = {"company_id": cid, "credential_types": list(types), "status": status, "process_id": process_id,
           "step_run_id": step_run_id, "started_at": started_at, "finished_at": finished_at}
    store().put_run(run)
    return run


def _check_round(cid: str) -> None:
    """README 6.2: the round is `DONE` as soon as all its types are `ISSUED`; then, and only then, there is
    exactly one `CredentialsIssued` with the types of the round. A `CANCELLED` round stays as it is."""
    run = store().get_run(cid)
    if not run or run["status"] not in ("RUNNING", "FAILED"):
        return
    rows = [store().get_credential(cid, t) for t in run["credential_types"]]
    if not all(r and r["status"] == "ISSUED" for r in rows):
        return
    run.update(status="DONE", finished_at=now())
    store().put_run(run)
    events.publish(MODULE, "CredentialsIssued", {"companyId": cid, "credentialTypes": list(run["credential_types"])})


def _preconditions(cid: str) -> tuple[dict, dict, str]:
    """README 8.1: company, then wallet, then route. Returns (company, wallet, route name)."""
    company = neighbour_client.company(cid)
    if not company or not company.get("bpn") or company.get("status") not in ("REQUESTED", "ACTIVE"):
        raise errors.company_not_ready("company without BPN or not REQUESTED/ACTIVE")
    wallet = neighbour_client.wallet(cid)
    if not wallet or wallet.get("status") != "ACTIVE" or not wallet.get("did"):
        raise errors.wallet_not_ready("dataspace wallet not ACTIVE or without DID")
    route = routes.select_route(wallet)
    if route == CREDENTIAL_ISSUER and not wallet.get("didDocumentLocation"):
        raise errors.wallet_not_ready("wallet without location of the DID document")
    return company, wallet, route


# ---------------------------------------------------------------------------------- issue-credentials
def issue_credentials(request: IssueCredentials) -> StepResult[IssueResult]:
    """README 8.1."""
    cid = request.company_id
    types = list(request.credential_types or [CredentialType(t) for t in config.onboarding_types()])
    with store().transaction(cid):
        company, wallet, route_name = _preconditions(cid)
        rows = {t: store().get_credential(cid, t) for t in types}
        if any(r and r["status"] == "REVOCATION_PENDING" for r in rows.values()):
            raise errors.invalid_state("a credential waits for the confirmation of its revocation "
                                       "(confirm-revocation)", retryable=False)
        t_now = now()
        to_order = [t for t in types if _needs_order(rows[t], t_now)]
        if to_order:
            route = routes.get(route_name)
            ctx = {"company": company, "wallet": wallet, "route": route_name}
            route.prepare(ctx)
            for t in to_order:
                _order(ctx, route, rows[t], t)
        stored = {t: row for t in types if (row := store().get_credential(cid, t)) is not None}
        all_issued = all(r["status"] == "ISSUED" for r in stored.values())
        run = store().get_run(cid)
        if all_issued:
            started = run["started_at"] if run else now()
            finished = run["finished_at"] if run and run["status"] == "DONE" and run["finished_at"] else now()
            _put_run(cid, types, "DONE", request.process_id, request.step_run_id, started, finished)
        else:
            started = run["started_at"] if run and run["status"] == "RUNNING" else now()
            _put_run(cid, types, "RUNNING", request.process_id, request.step_run_id, started)
        result = IssueResult(company_id=cid, credentials=[
            CredentialOutcome(credential_type=t, status=stored[t]["status"]) for t in types])
        return (StepResult.done if all_issued else StepResult.running)(request, result)


def _needs_order(row: dict | None, t_now: dt.datetime) -> bool:
    """README 8.1 step 2: a type is ordered unless it is `ISSUED` or `REQUESTED` within `RESEND_AFTER_HOURS`."""
    if row is None:
        return True
    if row["status"] == "ISSUED":
        return False
    return not (row["status"] == "REQUESTED" and t_now - row["requested_at"] < config.resend_after())


def _order(ctx: dict, route: IssuerRoute, row: dict | None, ctype: str) -> None:
    """Sends the order through the route; only after success the row becomes `REQUESTED` (README 8.1 step 2)."""
    attempt = (row["attempt"] if row else 0) + 1
    request_ref, issuer_did = route.order(ctx, ctype, attempt)
    t = now()
    company, wallet = ctx["company"], ctx["wallet"]
    new = dict(row) if row else {"id": str(uuid.uuid4()), "company_id": company["id"], "credential_type": ctype,
                                 "created_at": t}
    new.update(route=ctx["route"], issuer_did=issuer_did, wallet_provider=wallet.get("provider"),
               bpn=company["bpn"].upper(), holder_did=wallet.get("did"), request_ref=request_ref, attempt=attempt,
               requested_at=t, issued_at=None, failed_at=None, revoked_at=None, failure_reason=None,
               revocation_reason=None)
    _change(new, "REQUESTED")


# ------------------------------------------------------------------------------------ revoke-credentials
def revoke_credentials(request: RevokeCredentials) -> StepResult[RevocationResult]:
    """README 8.2. No precondition on company or wallet; per given type (default MEMBERSHIP): `ISSUED` is revoked
    through the route of the order (or waits for OSP staff), `REQUESTED`/`FAILED` become `CANCELLED`."""
    cid, reason = request.company_id, request.reason
    types = list(request.credential_types or [CredentialType.MEMBERSHIP])
    revoked: list[CredentialType] = []
    cancelled: list[CredentialType] = []
    manual: list[CredentialType] = []
    with store().transaction(cid):
        for t in types:
            row = store().get_credential(cid, t)
            if row is None:
                continue
            if row["status"] == "ISSUED":
                if routes.get(row["route"]).revoke(row):
                    _change(row, "REVOKED", revoked_at=now(), revocation_reason=reason)
                    events.publish(MODULE, "CredentialRevoked", {"companyId": cid, "credentialType": t,
                                                                  "revocationReason": reason})
                    revoked.append(t)
                else:
                    _change(row, "REVOCATION_PENDING", revocation_reason=reason)
                    manual.append(t)
            elif row["status"] in ("REQUESTED", "FAILED"):
                routes.get(row["route"]).cancel(row)
                _change(row, "CANCELLED", revocation_reason=reason)
                cancelled.append(t)
            elif row["status"] == "REVOCATION_PENDING":
                manual.append(t)
        run = store().get_run(cid)
        if run and run["status"] == "RUNNING" and set(run["credential_types"]) & set(types):
            run.update(status="CANCELLED", finished_at=now())
            store().put_run(run)
    return StepResult.done(request, RevocationResult(company_id=cid, revoked=revoked, cancelled=cancelled,
                                                     manual_revocation=manual))


# -------------------------------------------------------------------------------------- status report
def report_status(kind: str, bpn: str, status: str, message: str | None = None) -> None:
    """README 7.4 steps 3 and 4 (the HTTP layer checks token and input and writes the audit entry)."""
    ctype = kind.upper()
    found = store().find_credential(bpn.upper(), ctype)
    if found is None:
        raise errors.unknown_request()
    cid = found["company_id"]
    with store().transaction(cid):
        row = store().get_credential(cid, ctype)
        if row is None:
            raise errors.unknown_request()
        state, ok = row["status"], status == "SUCCESSFUL"
        if state == "REQUESTED":
            if ok:
                _change(row, "ISSUED", message, issued_at=now())
                _check_round(cid)
            else:
                _fail(row, message)
        elif state == "ISSUED":
            if not ok:
                raise errors.invalid_state("credential is already issued")
        elif state == "FAILED":
            if ok:
                _change(row, "ISSUED", message, issued_at=now())
                _check_round(cid)
        elif state == "CANCELLED" and ok:
            _revoke_now(row)
        # REVOCATION_PENDING, REVOKED, and the remaining combinations: nothing


def validate_report(kind: str, body: object) -> IssuerReport:
    """README 7.4 step 2: an unknown kind is 404 `not-found` before the body is looked at; an invalid body is
    400 `validation`. The BPN comes back in upper case."""
    if kind not in CREDENTIAL_KINDS:
        raise errors.not_found("credentialKind must be bpn or membership")
    report = parse(IssuerReport, body)
    report.bpn = report.bpn.upper()
    return report


def receive_report(kind: str, body: object, claims: dict) -> None:
    """README 7.4 steps 2 to 4 for a report over HTTP: check the kind and the body, process, write the audit entry."""
    report = validate_report(kind, body)
    report_status(kind, report.bpn, report.status, report.message)
    audit(claims, "REPORT_CREDENTIAL_STATUS", None, f"{report.bpn}:{kind.upper()}", 204)


def audit(claims: dict, operation: str, company_id: str | None, object_ref: str, result: int) -> None:
    """Audit log entry of a changing operation over HTTP (README 5 `audit_entry`): identifiers only, no names."""
    store().append_audit({"id": str(uuid.uuid4()), "occurred_at": now(), "sub": claims.get("sub"),
                          "client_id": claims.get("azp"), "company_id": claims.get("company_id") or company_id,
                          "operation": operation, "object_ref": object_ref, "result": str(result)})


def _fail(row: dict, message: str | None) -> None:
    _change(row, "FAILED", message, failed_at=now(), failure_reason=_truncate(message, 1000))
    events.publish(MODULE, "CredentialIssuanceFailed", {
        "companyId": row["company_id"], "credentialType": row["credential_type"],
        "reason": _truncate(message, 200) or "issuance failed"})
    run = store().get_run(row["company_id"])
    if run and run["status"] == "RUNNING":
        run["status"] = "FAILED"
        store().put_run(run)


def _revoke_now(row: dict) -> None:
    """A success report for a `CANCELLED` row: revoked immediately (README 6.1 last row, 7.4)."""
    if routes.get(row["route"]).revoke(row):
        _change(row, "REVOKED", revoked_at=now())
        events.publish(MODULE, "CredentialRevoked", {
            "companyId": row["company_id"], "credentialType": row["credential_type"],
            "revocationReason": row.get("revocation_reason") or "OTHER"})
    else:
        _change(row, "REVOCATION_PENDING")


# ---------------------------------------------------------------------------------- confirm-revocation
def confirm_revocation(credential_id: str, request: ConfirmRevocation, claims: dict) -> CredentialDetail:
    """README 7.3: `REVOCATION_PENDING` becomes `REVOKED` (history with the note, audit entry with `sub` of the
    person, `CredentialRevoked`); `REVOKED` stays as it is (200); any other status is 409 `invalid-state`."""
    note = request.note
    found = store().get_credential_by_id(credential_id)
    if found is None:
        raise errors.not_found("unknown credential")
    with store().transaction(found["company_id"]):
        row = store().get_credential_by_id(credential_id)
        if row is None:
            raise errors.not_found("unknown credential")
        if row["status"] == "REVOKED":
            return CredentialDetail.model_validate(row)
        if row["status"] != "REVOCATION_PENDING":
            raise errors.invalid_state(f"credential is {row['status']}, not REVOCATION_PENDING")
        _change(row, "REVOKED", note, revoked_at=now())
        audit(claims, "CONFIRM_REVOCATION", None, row["id"], 200)
        events.publish(MODULE, "CredentialRevoked", {
            "companyId": row["company_id"], "credentialType": row["credential_type"],
            "revocationReason": row.get("revocation_reason") or "OTHER"})
        return CredentialDetail.model_validate(row)

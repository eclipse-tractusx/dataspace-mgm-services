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
"""The steps of C3-M2 for Process Orchestration (README 8): input = JSON body incl. processId and stepRunId,
answer = `StepReply` (FRAMEWORK 4.4)."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from features.csp_connection.managers import csp_client, store
from features.csp_connection.managers.store import Registration
from features.csp_connection.models import errors
from features.csp_connection.models.errors import MODULE
from features.csp_connection.models.schemas import Membership
from features.csp_connection.services.common import (
    COUNTRY,
    StepInputJson,
    StepReply,
    identifier_list,
    optional_text,
    registered_row,
    require_text,
    row_bpn,
    step_reply,
)
from features.csp_connection.services.registration_state import registration_answer
from portal_common import events


def register_company(input: StepInputJson) -> StepReply:
    """Step register-company (README 8.1)."""
    company_id = require_text(input, "companyId")
    legal_name = require_text(input, "legalName")
    country = require_text(input, "country")
    if not COUNTRY.match(country):
        raise errors.validation("country must be two upper-case letters")
    ebwoid, euid = optional_text(input, "ebwoid"), optional_text(input, "euid")
    identifiers = identifier_list(input.get("identifiers"))
    if not (ebwoid or euid or identifiers):
        raise errors.validation("at least ebwoid, euid or an entry in identifiers is required (README 6.5)")

    # Repetitions (README 6.4): a registered company returns its BPN, a running operation stays
    # RUNNING; neither calls the CSP again. PENDING without an operation id has no running
    # operation, so it calls the CSP again like a new one (OPEN-QUESTIONS 19). From
    # TRANSFERRED_AWAY the only way back is transfer-company (README 6.1, OPEN-QUESTIONS 6).
    # New or FAILED: call the CSP (again).
    row = store.get_registration(company_id)
    if row is not None and row.status == "REGISTERED" and row.bpn:
        return step_reply(input, {"bpn": row.bpn})
    if row is not None and row.status == "PENDING" and row.pending_operation_id:
        return step_reply(input, state="RUNNING")
    if row is not None and row.status == "TRANSFERRED_AWAY":
        raise errors.invalid_state("the company moved to another OSP; a return uses transfer-company")

    payload: dict[str, Any] = {"legalName": legal_name, "country": country, "identifiers": identifiers}
    payload |= {k: v for k, v in (("ebwoid", ebwoid), ("euid", euid)) if v}
    if isinstance(input.get("address"), dict):
        payload["address"] = input["address"]
    status, answer = csp_client.call("register-company", "POST", "/companies", payload, company_id=company_id)
    return registration_answer(input, company_id, status, answer)


def transfer_company(input: StepInputJson) -> StepReply:
    """Step transfer-company (README 8.2): the company moves to this OSP."""
    company_id = require_text(input, "companyId")
    bpn = require_text(input, "bpn")
    ebwoid, euid = optional_text(input, "ebwoid"), optional_text(input, "euid")
    identifiers = identifier_list(input.get("identifiers"))

    row = store.get_registration(company_id)
    if row is not None and row.status == "REGISTERED":
        if row.bpn != bpn:
            raise errors.invalid_state(f"company {company_id} is registered with another BPN")
        return step_reply(input, {"bpn": bpn})
    if row is not None and row.status == "PENDING" and row.pending_operation_id:   # OPEN-QUESTIONS 19
        return step_reply(input, state="RUNNING")

    if row is not None and row.status == "TRANSFERRED_AWAY":
        row.returning = True   # a rejection keeps TRANSFERRED_AWAY (mark_rejected)
        store.save(row)
    payload: dict[str, Any] = {k: v for k, v in (("ebwoid", ebwoid), ("euid", euid)) if v}
    if identifiers:
        payload["identifiers"] = identifiers
    status, answer = csp_client.call("transfer-company", "POST", f"/companies/{bpn}/transfer", payload,
                                     company_id=company_id, bpn=bpn)
    return registration_answer(input, company_id, status, answer)


def register_did(input: StepInputJson) -> StepReply:
    """Step register-did (README 8.3): DID in the directory BPN -> DID."""
    company_id = require_text(input, "companyId")
    did = require_text(input, "did")
    row = registered_row(company_id)
    bpn = row_bpn(row)
    if row.did != did:
        status, answer = csp_client.call("register-did", "PUT", f"/companies/{bpn}/did", {"did": did},
                                         company_id=company_id, bpn=bpn)
        csp_client.raise_for(status, answer)
        # a concurrent call may have stored it meanwhile: one event only
        _change_once(company_id, lambda r: r.did == did, lambda r: setattr(r, "did", did),
                     "CompanyDidRegistered", {"companyId": company_id, "bpn": bpn, "did": did})
    return step_reply(input, {"bpn": bpn, "did": did})


def update_company(input: StepInputJson) -> StepReply:
    """Step update-company (README 8.4): changed core data to the CSP. The module keeps no core
    data (README 5), so a repetition is recognised by the `stepRunId` (FRAMEWORK 4.4)."""
    company_id = require_text(input, "companyId")
    legal_name = require_text(input, "legalName")
    euid = optional_text(input, "euid")
    row = registered_row(company_id)
    bpn = row_bpn(row)
    step_run = optional_text(input, "stepRunId")
    if step_run and row.last_update_step_run == step_run:
        return step_reply(input)
    payload: dict[str, Any] = {"legalName": legal_name}
    if euid:
        payload["euid"] = euid
    if isinstance(input.get("address"), dict):
        payload["address"] = input["address"]
    status, answer = csp_client.call("update-company", "PATCH", f"/companies/{bpn}", payload,
                                     company_id=company_id, bpn=bpn)
    csp_client.raise_for(status, answer)
    # one event per stepRunId, also with a concurrent repetition
    _change_once(company_id, lambda r: bool(step_run) and r.last_update_step_run == step_run,
                 lambda r: setattr(r, "last_update_step_run", step_run),
                 "CompanyUpdatedAtCsp", {"companyId": company_id, "bpn": bpn})
    return step_reply(input)


def _membership(input: StepInputJson, member: bool) -> StepReply:
    """Steps register-membership and deregister-membership (README 8.5)."""
    company_id = require_text(input, "companyId")
    current = store.get_registration(company_id)
    if not member and current is not None and current.status == "TRANSFERRED_AWAY":
        # the new home OSP owns the membership now (FRAMEWORK 5.6 step 3): no call, no event
        if current.membership != "NONE":
            current.membership = "NONE"
            current.touch()
            store.save(current)
        return step_reply(input)
    row = registered_row(company_id)
    bpn = row_bpn(row)
    target: Membership = "REGISTERED" if member else "DEREGISTERED"
    if row.membership != target:
        operation = "register-membership" if member else "deregister-membership"
        status, answer = csp_client.call(operation, "PUT", f"/companies/{bpn}/membership", {"member": member},
                                         company_id=company_id, bpn=bpn)
        csp_client.raise_for(status, answer)
        # one event only, also with a concurrent call
        _change_once(company_id, lambda r: r.membership == target, lambda r: setattr(r, "membership", target),
                     "MembershipRegistered" if member else "MembershipDeregistered",
                     {"companyId": company_id, "bpn": bpn})
    return step_reply(input)


def register_membership(input: StepInputJson) -> StepReply:
    """Step register-membership (README 8.5)."""
    return _membership(input, True)


def deregister_membership(input: StepInputJson) -> StepReply:
    """Step deregister-membership (README 8.5)."""
    return _membership(input, False)


def register_connector(input: StepInputJson) -> StepReply:
    """Step register-connector (README 8.6): connector into the discovery of the CSP."""
    company_id = require_text(input, "companyId")
    connector_id = require_text(input, "connectorId")
    endpoint = require_text(input, "endpointUrl")
    if not endpoint.startswith("https://"):
        raise errors.validation("endpointUrl must be an HTTPS address")
    bpn = row_bpn(registered_row(company_id))
    # Call the CSP only for a new connector or a new address (README 6.4); the same call again
    # answers DONE without a call and without an event.
    con = store.get_connector(connector_id)
    if con is not None and con.status == "REGISTERED" and con.company_id != company_id:
        # Entering it under the new BPN would leave it listed under the old one as well (README 6.6;
        # OPEN-QUESTIONS 17): C6-M1 deregisters it first.
        raise errors.invalid_state(f"connector {connector_id} is registered for company {con.company_id}; "
                                   "deregister it there first")
    unchanged = (con is not None and con.status == "REGISTERED" and con.endpoint_url == endpoint
                 and con.company_id == company_id and con.bpn == bpn)
    if not unchanged:
        status, answer = csp_client.call("register-connector", "PUT", f"/companies/{bpn}/connectors/{connector_id}",
                                         {"endpointUrl": endpoint}, company_id=company_id, bpn=bpn)
        csp_client.raise_for(status, answer)
        with store.lock:
            now = store.get_connector(connector_id)
            if not (now is not None and now.status == "REGISTERED" and now.endpoint_url == endpoint
                    and now.company_id == company_id and now.bpn == bpn):   # one event only
                stamp = store.now()
                store.save(store.Connector(
                    connector_id=connector_id, company_id=company_id, bpn=bpn, endpoint_url=endpoint,
                    status="REGISTERED", registered_at=now.registered_at if now else stamp, updated_at=stamp))
                events.publish(MODULE, "ConnectorRegisteredAtCsp",
                               {"companyId": company_id, "bpn": bpn, "connectorId": connector_id})
    return step_reply(input, {"bpn": bpn, "connectorId": connector_id})


def deregister_connector(input: StepInputJson) -> StepReply:
    """Step deregister-connector (README 8.6): unknown or already removed -> DONE without a call."""
    company_id = require_text(input, "companyId")
    connector_id = require_text(input, "connectorId")
    # Unknown or already removed: DONE without a call (README 6.4). The result carries the BPN only
    # when it is known (OPEN-QUESTIONS 8). A known connector needs a REGISTERED company
    # (OPEN-QUESTIONS 7), and it must be the connector's host company (README 8.6), otherwise the
    # event would pair one company's id with another's BPN (OPEN-QUESTIONS 17).
    con = store.get_connector(connector_id)
    if con is None or con.status == "DEREGISTERED":
        row = store.get_registration(company_id)
        bpn = con.bpn if con else (row.bpn if row else None)
        return step_reply(input, {"connectorId": connector_id} | ({"bpn": bpn} if bpn else {}))
    if con.company_id != company_id:
        raise errors.invalid_state(f"connector {connector_id} is registered for company {con.company_id}, "
                                   f"not for {company_id}")
    registered_row(company_id)
    status, answer = csp_client.call("deregister-connector", "DELETE",
                                     f"/companies/{con.bpn}/connectors/{connector_id}",
                                     company_id=company_id, bpn=con.bpn)
    csp_client.raise_for(status, answer)
    with store.lock:
        current = store.get_connector(connector_id)   # read again: a concurrent call may have removed it
        if current is not None and current.status == "REGISTERED":   # one event only
            current.status, current.updated_at = "DEREGISTERED", store.now()
            store.save(current)
            events.publish(MODULE, "ConnectorDeregisteredAtCsp",
                           {"companyId": company_id, "bpn": con.bpn, "connectorId": connector_id})
    return step_reply(input, {"bpn": con.bpn, "connectorId": connector_id})


def _change_once(company_id: str, done: Callable[[Registration], bool], change: Callable[[Registration], None],
                 event: str, data: dict[str, str]) -> None:
    """Applies `change` to the stored row and publishes `event`, unless `done` says another call already did:
    read, check, change and event under `store.lock`, so concurrent repetitions publish once (FRAMEWORK 4.4)."""
    with store.lock:
        row = store.get_registration(company_id)
        if row is None or done(row):
            return
        change(row)
        row.touch()
        store.save(row)
        events.publish(MODULE, event, data)

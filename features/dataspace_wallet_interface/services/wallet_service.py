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
"""Business logic of C4-M2: the single clock, the store, the audit log and the step log.

The controllers stay a thin HTTP layer and `interface.py` the public functions; the rules of the wallet
(README 6, 8) live here. Every time read of the module goes through `now()` so that tests can move the
clock. `account_service` imports this file, so this file loads it by name only inside functions
(`optional_module`); the provider adapters are `managers/providers/`.
"""
from __future__ import annotations

import datetime as dt
import importlib
import logging
import threading
import uuid
from types import ModuleType

from portal_common import events

from ..managers import config, crypto, neighbour_client, providers
from ..managers import did_resolver as did
from ..managers.wallet_store import DatabaseStore, WalletStore
from ..models import MODULE
from ..models.api import WalletStepReply, WalletStepResult
from ..models.callbacks import callback_body_problem, callback_document_valid
from ..models.errors import problem as _problem
from ..models.value_sets import StepState

log = logging.getLogger(__name__)

PROVIDERS = ("SAP_DIV", "IDENTITY_HUB", "CSP")
HOLDER_ACCESS, STS_ACCESS = "HOLDER_ACCESS", "STS_ACCESS"

_store: WalletStore | None = None
_store_lock = threading.Lock()


def now() -> dt.datetime:
    """The clock of the module: timezone-aware UTC. All time reads go through this function."""
    return dt.datetime.now(dt.UTC)


def get_store() -> WalletStore:
    """The active store: the repository of the feature's tables."""
    global _store
    with _store_lock:
        if _store is None:
            _store = DatabaseStore()
        return _store


def optional_module(name: str) -> ModuleType | None:
    """`features.dataspace_wallet_interface.services.<name>` if the file exists, else None; a broken import
    still raises."""
    full = f"{__package__}.{name}"
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as error:
        if error.name == full:
            return None
        raise


def reset() -> None:
    """Stop the timer, empty the tables and forget the key cache and the state of the provider stand-ins."""
    stop_timer()
    get_store().reset()
    crypto.reset()
    providers.reset()


def audit(claims: dict | str | None, operation: str, company_id: str | None, object_id: str | None) -> None:
    """Write an audit entry (README 5 `audit_log`). `claims` is the token claims dict of an HTTP call, or
    the name of the calling module for an in-process call (then the entry holds that name). No secrets."""
    if isinstance(claims, dict):
        sub, azp = claims.get("sub"), claims.get("azp")
    else:
        sub = azp = claims
    get_store().append_audit({"occurred_at": now(), "sub": sub, "azp": azp, "company_id": company_id,
                              "operation": operation, "object_id": object_id})


def log_step(input: dict, step: str, object_id: str | None, state: StepState) -> None:
    """Write a step-log entry (README 5 `step_log`)."""
    get_store().append_step_log({"step_run_id": input.get("stepRunId"), "process_id": input.get("processId"),
                                 "step": step, "object_id": object_id, "state": state, "occurred_at": now()})


# --------------------------------------------------------------------------------------- helpers
def when(value: object) -> dt.datetime | None:
    """A timezone-aware datetime from a datetime or an ISO string, None if there is none."""
    if isinstance(value, str):
        try:
            value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, dt.datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=dt.UTC)


def iso(value: object) -> str | None:
    """ISO 8601 text of a datetime or an ISO string, None if there is none."""
    moment = when(value)
    return moment.isoformat() if moment else None


def providers_module() -> ModuleType:
    """The provider adapters of C4-M2 (`managers/providers/`)."""
    return providers


def enabled_providers() -> list[str]:
    """README 4: `ENABLED_PROVIDERS`, empty = `SAP_DIV,IDENTITY_HUB,CSP`."""
    return list(providers.enabled())


def default_provider() -> str:
    """README 4: `DEFAULT_PROVIDER`, empty = `CSP`."""
    return providers.default_provider()


def get_company(company_id: str) -> dict | None:
    """The company of C3-M1 (`managers/neighbour_client.py`)."""
    return neighbour_client.get_company(company_id)


def get_wallet(company_id: str) -> dict | None:
    """The wallet row of a company."""
    return get_store().get_wallet(company_id)


def wallet_secret(wallet_id: str, kind: str) -> dict | None:
    """The decrypted secret of a wallet: `{url, client_id, secret}`, None if there is none."""
    row = get_store().get_secret(wallet_id, kind)
    if row is None:
        return None
    return {"url": row["url"], "client_id": row["client_id"],
            "secret": crypto.decrypt(row["secret_encrypted"], row["nonce"], row["key_version"])}


def _store_secret(wallet_id: str, kind: str, access: dict) -> None:
    """Encrypt and store `{url, client_id, secret}` (README 5 `wallet_secret`)."""
    ciphertext, nonce, key_version = crypto.encrypt(access["secret"])
    get_store().put_secret(wallet_id, kind, access["url"], access["client_id"], ciphertext, nonce, key_version)


def _save(wallet: dict) -> dict:
    wallet["changed_at"] = now()
    get_store().put_wallet(wallet)
    return wallet


def did_web_location(did_value: str | None) -> str | None:
    """Location of the DID document by the `did:web` rules."""
    if not did_value or not did_value.lower().startswith("did:web:"):
        return None
    parts = did_value.split(":")[2:]
    return "https://" + "/".join(parts) + "/did.json" if parts else None


def credential_service_url(document: dict) -> str | None:
    """Endpoint of the service of type `CredentialService` in a DID document, if there is one."""
    services = document.get("service") if isinstance(document, dict) else None
    if isinstance(services, dict):
        services = [services]
    for entry in services if isinstance(services, list) else []:
        kind = entry.get("type") if isinstance(entry, dict) else None
        if kind == did.CREDENTIAL_SERVICE or (isinstance(kind, list) and did.CREDENTIAL_SERVICE in kind):
            endpoint = entry.get("serviceEndpoint")
            if isinstance(endpoint, str) and endpoint:
                return endpoint
    return None


# ----------------------------------------------------------------------------- events and status
def _wallet_created(wallet: dict) -> None:
    events.publish(MODULE, "DataspaceWalletCreated", {
        "companyId": wallet["company_id"], "did": wallet["did"], "walletId": wallet["id"],
        "provider": wallet["provider"], "didDocumentLocation": wallet["did_document_location"],
        "bpn": wallet["bpn"]})


def _fail(wallet: dict, reason: str) -> dict:
    """Status `FAILED` with the reason and the event `DataspaceWalletFailed` (README 6.2, 10)."""
    wallet.update(status="FAILED", failure_reason=reason, next_check_at=None)
    _save(wallet)
    events.publish(MODULE, "DataspaceWalletFailed", {
        "companyId": wallet["company_id"], "walletId": wallet["id"], "provider": wallet["provider"],
        "reason": reason})
    return wallet


def _activate(wallet: dict, document: dict) -> dict:
    """README 6.4 step 4: `did_validated_at`, the credential service of the document, status `ACTIVE`."""
    moment = now()
    wallet.update(status="ACTIVE", did_validated_at=moment, activated_at=moment, next_check_at=None,
                  credential_service_url=credential_service_url(document) or wallet.get("credential_service_url"))
    _save(wallet)
    _wallet_created(wallet)
    return wallet


def check_did(wallet: dict) -> dict:
    """One DID check of a `VALIDATING` wallet (README 6.4). Call it inside `transaction(company_id)`.

    Wrong form: `FAILED` `DID_MISMATCH`. Not resolvable: the next attempt after
    `DID_VALIDATION_INTERVAL_MINUTES`, after `DID_VALIDATION_MAX_HOURS` from `validating_since` `FAILED`
    `DID_NOT_RESOLVABLE`. Invalid content: `FAILED` `INVALID_DID_DOCUMENT`. Otherwise `ACTIVE`."""
    if not did.check_form(wallet["provider"], wallet["did"], wallet["bpn"]):
        return _fail(wallet, "DID_MISMATCH")
    document = did.resolve(wallet["did"])
    moment = now()
    if document is None:
        started = when(wallet.get("validating_since")) or moment
        if moment >= started + dt.timedelta(hours=config.did_validation_max_hours()):
            return _fail(wallet, "DID_NOT_RESOLVABLE")
        wallet["next_check_at"] = moment + dt.timedelta(minutes=config.did_validation_interval_minutes())
        return _save(wallet)
    if did.check_document(wallet["provider"], wallet["did"], document):
        return _fail(wallet, did.INVALID_DID_DOCUMENT)
    return _activate(wallet, document)


# ------------------------------------------------------------------------------------ create-wallet
def _validate_create_input(input: dict) -> tuple[str, str | None]:
    """README 8.1 step 1: the input of the step; returns `(companyId, provider or None)`."""
    if not isinstance(input, dict):
        raise _problem(400, "validation", "the input must be a JSON object")
    for name in ("processId", "stepRunId", "companyId"):
        value = input.get(name)
        try:
            if not isinstance(value, str):
                raise ValueError
            uuid.UUID(value)
        except ValueError:
            raise _problem(400, "validation", f"{name} must be a UUID") from None
    provider = input.get("provider")
    if provider is None:
        return input["companyId"], None
    if provider == "BRING_YOUR_OWN":
        raise _problem(400, "provider-not-enabled", "BRING_YOUR_OWN is not available yet")
    if provider not in PROVIDERS:
        raise _problem(400, "validation", "provider must be SAP_DIV, IDENTITY_HUB or CSP")
    return input["companyId"], provider


def _choose_provider(requested: str | None) -> str:
    """README 6.1: the provider of the input, otherwise `DEFAULT_PROVIDER`; it must be enabled."""
    provider = requested or default_provider()
    if provider not in enabled_providers():
        raise _problem(400, "provider-not-enabled", f"{provider} is not in ENABLED_PROVIDERS")
    return provider


def _new_wallet(company_id: str, bpn: str, provider: str) -> dict:
    moment = now()
    return {"id": str(uuid.uuid4()), "company_id": company_id, "bpn": bpn, "provider": provider,
            "status": "REQUESTED", "failure_reason": None, "did": None, "did_document_location": None,
            "credential_service_url": None, "provider_ref": None, "control_challenge_id": None, "attempt": 1,
            "provider_ordered_at": None, "validating_since": None, "did_validated_at": None,
            "next_check_at": None, "activated_at": None, "created_at": moment, "changed_at": moment}


def _reset_for_new_attempt(wallet: dict, provider: str) -> dict:
    """README 6.2: a new attempt after `FAILED` deletes the secrets, clears `did` and the progress fields."""
    get_store().delete_secrets(wallet["id"])
    wallet.update(provider=provider, status="REQUESTED", failure_reason=None, did=None,
                  did_document_location=None, credential_service_url=None, provider_ref=None,
                  provider_ordered_at=None, validating_since=None, did_validated_at=None, next_check_at=None,
                  activated_at=None, attempt=int(wallet.get("attempt") or 1) + 1)
    return _save(wallet)


def _order(wallet: dict, company: dict) -> dict:
    """README 8.1 step 4: the order to the adapter. `provider_ordered_at` is set only after it accepted."""
    answer = providers.get(wallet["provider"]).order_wallet({
        "company_id": wallet["company_id"], "bpn": wallet["bpn"], "company_name": company.get("name"),
        "attempt": wallet["attempt"], "wallet_id": wallet["id"]})
    # An in-process stand-in may already have called back while ordering: continue from the stored row.
    wallet = get_store().get_wallet(wallet["company_id"]) or wallet
    moment = now()
    if answer.get("result") == "CREATED":
        for kind, access in (answer.get("secrets") or {}).items():
            _store_secret(wallet["id"], kind, access)
        wallet.update(status="VALIDATING", did=answer["did"], did_document_location=answer.get("did_document_location"),
                      credential_service_url=answer.get("credential_service_url"),
                      provider_ref=answer.get("provider_ref"), provider_ordered_at=moment,
                      validating_since=moment, next_check_at=moment)
        _save(wallet)
        return check_did(wallet)           # README 8.1 step 5: try the DID check at once
    wallet["provider_ordered_at"] = wallet.get("provider_ordered_at") or moment
    wallet["provider_ref"] = wallet.get("provider_ref") or wallet["bpn"]
    return _save(wallet)


def _step_result(wallet: dict) -> WalletStepResult:
    """README 8.1 result (openapi `StepResultWallet`); no secrets, empty optional fields are left out."""
    optional = {"did": wallet.get("did"), "did_document_location": wallet.get("did_document_location"),
                "failure_reason": wallet.get("failure_reason")}
    return WalletStepResult(wallet_id=wallet["id"], company_id=wallet["company_id"], provider=wallet["provider"],
                            status=wallet["status"], **{name: value for name, value in optional.items() if value})


def create_wallet(input: dict) -> WalletStepReply:
    """The step `create-wallet` (README 8.1). Long-running: `RUNNING` unless the wallet was already `ACTIVE`."""
    company_id, requested = _validate_create_input(input)
    store = get_store()
    with store.transaction(company_id):
        company = get_company(company_id)
        if company is None:
            raise _problem(404, "not-found", "company not found")
        if not company.get("bpn"):
            raise _problem(409, "company-not-ready", "the company has no BPN yet")
        bpn = str(company["bpn"]).upper()
        wallet = store.get_wallet(company_id)
        other = store.find_wallet_by_bpn(bpn)
        if (wallet and wallet["bpn"] != bpn) or (other and other["company_id"] != company_id):
            raise _problem(409, "conflict", "the BPN does not match the existing wallets")
        state: StepState = "RUNNING"
        if wallet is None:
            wallet = _save(_new_wallet(company_id, bpn, _choose_provider(requested)))
            wallet = _order(wallet, company)
        elif wallet["status"] == "ACTIVE":
            state = "DONE"
        elif wallet["status"] == "FAILED":
            wallet = _reset_for_new_attempt(wallet, _choose_provider(requested))
            wallet = _order(wallet, company)
        elif wallet["status"] == "REQUESTED" and not wallet.get("provider_ordered_at"):
            wallet = _order(wallet, company)
        # REQUESTED with `provider_ordered_at` and VALIDATING: nothing else (RUNNING)
        log_step(input, "create-wallet", company_id, state)
        return WalletStepReply(step_run_id=input["stepRunId"], state=state, result=_step_result(wallet))


# --------------------------------------------------------------------------- SAP DIV callbacks
def _sap_div_location(bpn: str, did_value: str) -> str | None:
    base = config.sap_div_did_document_base_url()
    return f"{base}/{bpn}/did.json" if base else did_web_location(did_value)


def accept_wallet_callback(bpn: str, body: dict, claims: dict | str | None) -> None:
    """The wallet callback of SAP DIV (README 7.6 steps 1 to 6). Returns None (the route answers 204);
    raises `Problem` for 400, 404 and 409. Every accepted callback, also a duplicate, is audited."""
    problem = callback_body_problem(body)
    if problem:
        raise _problem(400, "validation", problem)
    store = get_store()
    found = store.find_wallet_by_bpn(bpn)
    if found is None or found["provider"] != "SAP_DIV":
        raise _problem(404, "not-found", "no SAP DIV wallet for this BPN")
    with store.transaction(found["company_id"]):
        wallet = store.get_wallet(found["company_id"])
        if wallet is None or wallet["provider"] != "SAP_DIV":
            raise _problem(404, "not-found", "no SAP DIV wallet for this BPN")
        announced = body["did"]
        if wallet["status"] in ("VALIDATING", "ACTIVE"):
            if (wallet.get("did") or "").lower() != announced.lower():
                raise _problem(409, "conflict", "the wallet already has another DID")
        elif wallet["status"] != "REQUESTED":
            raise _problem(409, "invalid-state", "the wallet is not waiting for a callback; a new attempt is needed")
        elif not did.check_form("SAP_DIV", announced, wallet["bpn"]):
            _fail(wallet, "DID_MISMATCH")
        elif not callback_document_valid(body["didDocument"]):
            _fail(wallet, did.INVALID_DID_DOCUMENT)
        else:
            details = body["authenticationDetails"]
            _store_secret(wallet["id"], HOLDER_ACCESS, {"url": details["authenticationServiceUrl"],
                                                        "client_id": details["clientID"],
                                                        "secret": details["clientSecret"]})
            moment = now()
            wallet.update(status="VALIDATING", did=announced,
                          did_document_location=_sap_div_location(wallet["bpn"], announced),
                          credential_service_url=credential_service_url(body["didDocument"]),
                          validating_since=moment, next_check_at=moment)
            _save(wallet)
            check_did(wallet)              # README 7.6 step 6: the check starts right after the commit
        audit(claims, "SUBMIT_WALLET_CALLBACK", wallet["company_id"], wallet["id"])


# -------------------------------------------------------------------------- scheduled tasks
def _timer_pass_requested(moment: dt.datetime) -> None:
    """README 6.10 callback deadline: `REQUESTED` with an order older than the deadline."""
    deadline = dt.timedelta(minutes=config.provider_callback_timeout_minutes())
    store = get_store()
    for candidate in store.list_wallets(["REQUESTED"]):
        ordered = when(candidate.get("provider_ordered_at"))
        if ordered is None or moment - ordered <= deadline:
            continue
        with store.transaction(candidate["company_id"]):
            wallet = store.get_wallet(candidate["company_id"])
            if wallet and wallet["status"] == "REQUESTED" and when(wallet.get("provider_ordered_at")) == ordered:
                _fail(wallet, "PROVIDER_TIMEOUT")


def _timer_pass_validating(moment: dt.datetime) -> None:
    """README 6.10 DID check: `VALIDATING`, no `did_validated_at`, `next_check_at` reached."""
    store = get_store()
    for candidate in store.list_wallets(["VALIDATING"]):
        due = when(candidate.get("next_check_at"))
        if candidate.get("did_validated_at") or due is None or due > moment:
            continue
        with store.transaction(candidate["company_id"]):
            wallet = store.get_wallet(candidate["company_id"])
            if wallet and wallet["status"] == "VALIDATING" and not wallet.get("did_validated_at"):
                check_did(wallet)


def run_timer_once() -> None:
    """One pass of every scheduled task (README 6.10). The background thread calls it every
    `TIMER_INTERVAL_SECONDS`; tests call it directly."""
    moment = now()
    _timer_pass_requested(moment)
    _timer_pass_validating(now())
    accounts = optional_module("account_service")
    if accounts is not None and hasattr(accounts, "run_tasks"):
        accounts.run_tasks()


_timer: threading.Thread | None = None
_timer_stop = threading.Event()


def _timer_loop(stop: threading.Event) -> None:
    while not stop.wait(config.timer_interval_seconds()):
        try:
            run_timer_once()
        except Exception:  # noqa: BLE001 - a failing pass must not end the timer
            log.exception("scheduled tasks of C4-M2 failed")


def start_timer() -> None:
    """Start the background thread of the scheduled tasks if it is not running."""
    global _timer, _timer_stop
    if _timer is not None and _timer.is_alive():
        return
    _timer_stop = threading.Event()
    _timer = threading.Thread(target=_timer_loop, args=(_timer_stop,), name="c4-m2-timer", daemon=True)
    _timer.start()


def stop_timer() -> None:
    """Stop the background thread (used by `reset()`)."""
    global _timer
    _timer_stop.set()
    _timer = None


providers.on_callback("wallet-created", accept_wallet_callback)

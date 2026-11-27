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
#################################################################################
"""Transactions and steps (C5-M1 5, 6.1, 6.2, 7.5, 7.8), claims, verification attestation, audit log."""

import base64
import hashlib
import hmac
import json
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from urllib.parse import quote

from cryptography.hazmat.primitives.asymmetric import ec

from common import jwe
from common.jose import public_jwk, random_token, sha256_hex, sign_jws
from connector import checks, config
from connector.errors import VerificationError

PID_CLAIMS = ["given_name", "family_name", "birthdate", "issuing_country"]
MANDATE_CLAIMS = ["representative", "represented", "representation_type", "role", "valid_until"]
LPID_CLAIMS = ["legal_name", "ebwoid", "euid", "address", "country"]
TYPES = {"pid": "PID", "mandate": "MANDATE", "lpid": "LPID"}
CLAIMS = {"pid": PID_CLAIMS, "mandate": MANDATE_CLAIMS, "lpid": LPID_CLAIMS}


def credential_query(cid: str) -> dict:
    return {
        "id": cid,
        "format": "dc+sd-jwt",
        "meta": {"vct_values": [config.VCT[TYPES[cid]]]},
        "claims": [{"path": [name]} for name in CLAIMS[cid]],
    }


@dataclass
class Step:
    name: str  # person or company
    wallet: str  # EUDI_WALLET or BUSINESS_WALLET
    credential_ids: list[str]
    request_id: str = field(default_factory=lambda: random_token(16))
    nonce: str = field(default_factory=random_token)
    state: str = field(default_factory=random_token)
    enc_key: ec.EllipticCurvePrivateKey = field(default_factory=lambda: ec.generate_private_key(ec.SECP256R1()))
    status: str = "CREATED"

    @property
    def query(self) -> dict:
        return {"credentials": [credential_query(cid) for cid in self.credential_ids]}

    @property
    def request_uri(self) -> str:
        return f"{config.PUBLIC_URL}/openid4vp/requests/{self.request_id}"

    @property
    def link_params(self) -> str:
        return f"client_id={quote(config.WALLET_CLIENT_ID, safe='')}&request_uri={quote(self.request_uri, safe='')}"


@dataclass
class Transaction:
    client: dict
    redirect_uri: str
    scopes: list[str]
    state: str
    nonce: str
    code_challenge: str
    browser_hash: str
    steps: list[Step]
    id: str = field(default_factory=lambda: random_token(16))
    current: int = 0
    status: str = "PENDING"
    failure_reason: str | None = None
    created: float = field(default_factory=time.time)
    expires: float = 0.0
    verified_at: int | None = None
    presented: dict = field(default_factory=dict)  # credential ID -> checks.Presented
    claims: dict | None = None
    sub: str | None = None
    attestation: str | None = None
    code_hash: str | None = None
    code_expires: float = 0.0
    access_hash: str | None = None
    access_expires: float = 0.0
    code_used: bool = False

    @property
    def step(self) -> Step | None:
        return self.steps[self.current] if self.status == "PENDING" else None

    def refresh(self) -> None:
        """Expiry per 6.2."""
        now = time.time()
        if self.status in ("PENDING", "VERIFIED") and self.expires < now:
            self.status, self.failure_reason = "EXPIRED", "EXPIRED"
        elif self.status == "CODE_ISSUED" and self.code_expires < now:
            self.status = "EXPIRED"
        if self.status in ("FAILED", "EXPIRED"):
            self.presented.clear()


transactions: dict[str, Transaction] = {}
requests: dict[str, tuple[str, int]] = {}
access_tokens: dict[str, str] = {}


def purge() -> None:
    limit = time.time() - 600
    for tx_id, tx in list(transactions.items()):
        if tx.expires < limit and tx.access_expires < time.time():
            for step in tx.steps:
                requests.pop(step.request_id, None)
            if tx.access_hash:
                access_tokens.pop(tx.access_hash, None)
            del transactions[tx_id]


def create(client: dict, params: dict, scopes: list[str], browser_value: str) -> Transaction:
    purge()
    steps = [Step("person", "EUDI_WALLET", ["pid", "mandate"] if "representation" in scopes else ["pid"])]
    if "company" in scopes:
        steps.append(Step("company", "BUSINESS_WALLET", ["lpid"]))
    tx = Transaction(
        client=client,
        redirect_uri=params["redirect_uri"],
        scopes=scopes,
        state=params.get("state", ""),
        nonce=params["nonce"],
        code_challenge=params["code_challenge"],
        browser_hash=sha256_hex(browser_value),
        steps=steps,
        expires=time.time() + config.TRANSACTION_TTL_SECONDS,
    )
    transactions[tx.id] = tx
    for index, step in enumerate(steps):
        requests[step.request_id] = (tx.id, index)
    log(tx, "created")
    return tx


def for_request(request_id: str) -> tuple[Transaction, Step] | None:
    entry = requests.get(request_id)
    if not entry or entry[0] not in transactions:
        return None
    tx = transactions[entry[0]]
    tx.refresh()
    if tx.status != "PENDING" or tx.current != entry[1]:
        return None
    return tx, tx.steps[entry[1]]


def request_object(tx: Transaction, step: Step, wallet_nonce: str | None = None) -> str:
    metadata = {
        "client_name": tx.client.get("name", tx.client["clientId"]),
        "vp_formats_supported": {"dc+sd-jwt": {"sd-jwt_alg_values": ["ES256"], "kb-jwt_alg_values": ["ES256"]}},
    }
    if config.RESPONSE_MODE == "direct_post.jwt":
        enc_jwk = {**public_jwk(step.enc_key), "kid": step.request_id, "use": "enc", "alg": "ECDH-ES"}
        metadata["jwks"] = {"keys": [enc_jwk]}
        metadata["encrypted_response_enc_values_supported"] = ["A128GCM", "A256GCM"]
        # Names of OpenID4VP drafts before 1.0, for wallets that still read them.
        metadata["authorization_encrypted_response_alg"] = "ECDH-ES"
        metadata["authorization_encrypted_response_enc"] = "A128GCM"
    now = int(time.time())
    payload = {
        "aud": "https://self-issued.me/v2",
        "iat": now,
        "exp": int(tx.expires),
        "client_id": config.WALLET_CLIENT_ID,
        "response_type": "vp_token",
        "response_mode": config.RESPONSE_MODE,
        "response_uri": f"{config.PUBLIC_URL}/openid4vp/responses/{step.request_id}",
        "nonce": step.nonce,
        "state": step.state,
        "dcql_query": step.query,
        "client_metadata": metadata,
    }
    if wallet_nonce:
        payload["wallet_nonce"] = wallet_nonce
    if step.status == "CREATED":
        step.status = "REQUEST_RETRIEVED"
    return sign_jws({"typ": "oauth-authz-req+jwt", "x5c": config.REQUEST_X5C}, payload, config.SIGNING_KEY)


def fail(tx: Transaction, reason: str, detail: str) -> None:
    tx.status, tx.failure_reason = "FAILED", reason
    tx.steps[tx.current].status = "FAILED"
    tx.presented.clear()
    print(f"Transaction {tx.id}: FAILED {reason} ({detail})", flush=True)
    log(tx, "failed")


def receive(tx: Transaction, step: Step, form: dict) -> None:
    """Response of a wallet to a step (7.8 steps 2 to 6)."""
    if "error" in form:
        matches = form.get("state") == step.state
        print(
            f"Transaction {tx.id}: wallet reports {form['error']!r}: {form.get('error_description', '')!r}"
            f" (state {'matches' if matches else 'missing or does not match'})",
            flush=True,
        )
        if matches:
            fail(tx, "WALLET_ERROR", f"{form['error']}: {form.get('error_description', '')}")
        return
    try:
        if config.RESPONSE_MODE == "direct_post.jwt":
            if "response" not in form:
                raise VerificationError("INVALID_RESPONSE", "encrypted response expected")
            try:
                _, plaintext = jwe.decrypt(form["response"], step.enc_key)
                parameters = json.loads(plaintext)
            except (ValueError, KeyError, TypeError) as exc:
                raise VerificationError("INVALID_RESPONSE", f"cannot decrypt: {exc}") from None
        else:
            parameters = dict(form)
        if parameters.get("state") != step.state:
            raise VerificationError("INVALID_RESPONSE", "state does not match")
        vp_token = parameters.get("vp_token")
        if isinstance(vp_token, str):
            try:
                vp_token = json.loads(vp_token)
            except ValueError:
                raise VerificationError("INVALID_RESPONSE", "vp_token is not JSON") from None
        if not isinstance(vp_token, dict):
            raise VerificationError("INVALID_RESPONSE", "vp_token must be an object keyed by credential ID")
        unknown = set(vp_token) - set(step.credential_ids)
        if unknown:
            raise VerificationError("INVALID_RESPONSE", f"unknown credential IDs {sorted(unknown)}")
        counts = {cid: len(v) if isinstance(v, list) else type(v).__name__ for cid, v in vp_token.items()}
        print(f"Transaction {tx.id}: presentations per credential {counts}", flush=True)
        for cid in step.credential_ids:
            presentations = vp_token.get(cid)
            if isinstance(presentations, str):
                presentations = [presentations]
            if not presentations:
                raise VerificationError("MISSING_CREDENTIAL", f"{cid} missing")
            if not isinstance(presentations, list):
                raise VerificationError("INVALID_RESPONSE", f"{cid}: list of presentations expected")
            # A wallet should send one presentation per query; some send every matching credential.
            # Those that pass count; for PID and LPID the first, for the mandate see finalize().
            passed, errors = [], []
            for presentation in presentations:
                try:
                    if cid == "mandate":
                        passed.append(checks.receive_mandate(presentation, step.nonce))
                    else:
                        passed.append(checks.verify_listed(presentation, TYPES[cid], step.nonce, CLAIMS[cid]))
                except VerificationError as exc:
                    errors.append(exc)
            if not passed:
                raise errors[0]
            tx.presented[cid] = passed if cid == "mandate" else passed[0]
        step.status = "VERIFIED"
        if tx.current + 1 < len(tx.steps):
            tx.current += 1
        else:
            finalize(tx)
    except VerificationError as exc:
        fail(tx, exc.code, str(exc))


def finalize(tx: Transaction) -> None:
    """After the last step: representation check, claims, attestation (7.8 step 6)."""
    pid, lpid, mandates = (tx.presented.get(k) for k in ("pid", "lpid", "mandate"))
    representation = None
    if mandates:
        mandate, representation = choose_mandate(mandates, pid, lpid, tx.client)
        tx.presented["mandate"] = mandate
    tx.verified_at = int(time.time())
    verification_id = str(uuid.uuid4())
    claims = {"verification_id": verification_id}
    if "profile" in tx.scopes:
        claims.update({k: pid.claims[k] for k in ("given_name", "family_name", "birthdate") if k in pid.claims})
    if representation:
        trusted = "trust" in representation
        for key in ("result", "reasons", "type", "role", "valid_until", "company_id", "company_name", "issuer", "trust"):
            if key in representation and (trusted or key in ("result", "reasons", "issuer")):
                claims[f"representation_{key}"] = representation[key]
    if lpid is not None:
        company = lpid.claims
        for key in ("legal_name", "ebwoid", "euid", "country"):
            if key in company:
                claims[f"company_{key}"] = company[key]
        if isinstance(company.get("address"), dict):
            claims["company_address"] = company["address"]
    tx.claims = claims
    tx.sub = subject(tx, pid.claims)
    if "attestation" in tx.scopes:
        tx.attestation = attestation(tx, verification_id, representation)
    tx.status = "VERIFIED"
    log(tx, "verified", representation)
    tx.presented.clear()


def choose_mandate(mandates: list, pid, lpid, client: dict) -> tuple:
    """Of several mandates: a confirmed one, else a trusted one, else the first. Raises the first error
    if every mandate is trusted but expired, revoked or incomplete."""
    results, errors = [], []
    for mandate in mandates:
        try:
            results.append((mandate, checks.representation(mandate, pid, lpid, client, MANDATE_CLAIMS)))
        except VerificationError as exc:
            errors.append(exc)
    for wanted in (lambda r: r["result"] == "CONFIRMED", lambda r: "trust" in r, lambda r: True):
        chosen = next(((m, r) for m, r in results if wanted(r)), None)
        if chosen:
            return chosen
    raise errors[0]


def subject(tx: Transaction, pid_claims: dict) -> str:
    def norm(value) -> str:
        return unicodedata.normalize("NFC", str(value or "")).strip().casefold()

    material = "|".join(
        [tx.client["clientId"], norm(pid_claims.get("issuing_country"))]
        + [norm(pid_claims.get(k)) for k in ("family_name", "given_name", "birthdate")]
    )
    digest = hmac.new(config.SUBJECT_KEY, material.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def attestation(tx: Transaction, verification_id: str, representation: dict | None) -> str:
    """Verification attestation (section 9). With the company step its purpose is `onboarding` and the company comes
    from the LPID of the Business Wallet. Without it the purpose is `representation`: the company is the one the
    mandate names, with the data of the LPID inside the mandate if that LPID gave the trust (6.5 rule 4)."""
    pid, lpid, mandate = tx.presented["pid"], tx.presented.get("lpid"), tx.presented["mandate"]
    onboarding = lpid is not None
    source = lpid if onboarding else mandate.company
    company = {}
    if source is not None:
        company = {k: source.claims[k] for k in ("legal_name", "ebwoid", "euid", "country") if k in source.claims}
        if isinstance(source.claims.get("address"), dict):
            company["address"] = source.claims["address"]
    represented = {"confirmed": representation["result"] == "CONFIRMED"}
    represented.update({k: v for k, v in representation.items() if not onboarding or k not in ("company_id", "company_name")})
    evidence = [(pid, "EUDI_WALLET", False), (mandate, "EUDI_WALLET", False)]
    if source is not None:
        evidence.append((source, "BUSINESS_WALLET" if onboarding else "EUDI_WALLET", not onboarding))
    now = int(time.time())
    payload = {
        "iss": config.PUBLIC_URL,
        "sub": company.get("ebwoid") if onboarding else representation.get("company_id"),
        "aud": config.ATTESTATION_AUDIENCE,
        "iat": now,
        "exp": now + config.ATTESTATION_TTL_HOURS * 3600,
        "jti": verification_id,
        "attestation_version": "0.2",
        "purpose": "onboarding" if onboarding else "representation",
        "verified_at": tx.verified_at,
        "client_id": tx.client["clientId"],
        "person": {k: pid.claims[k] for k in ("given_name", "family_name")},
        "company": company,
        "representation": represented,
        "evidence": [
            {
                "type": item.credential_type,
                "vct": item.payload.get("vct"),
                "issuer": item.payload.get("iss"),
                "wallet": wallet,
                **({"carried_in": "MANDATE"} if carried else {}),
                "status_checked": item.status_checked,
            }
            for item, wallet, carried in evidence
        ],
    }
    # Missing values are left out, never null (9.1): no `sub` and no `company` for a mandate that is not trusted.
    payload = {k: v for k, v in payload.items() if v not in (None, {})}
    return sign_jws({"typ": "ebw-attestation+jwt", "kid": config.KID}, payload, config.SIGNING_KEY)


def issue_code(tx: Transaction) -> str:
    code = random_token(32)
    tx.code_hash = sha256_hex(code)
    tx.code_expires = time.time() + config.AUTH_CODE_TTL_SECONDS
    tx.status = "CODE_ISSUED"
    return code


def find_by_code(code: str) -> Transaction | None:
    digest = sha256_hex(code)
    return next((tx for tx in transactions.values() if tx.code_hash == digest), None)


def log(tx: Transaction, event: str, representation: dict | None = None) -> None:
    """Audit entry without personal data (C5-M1 5)."""
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        "transaction": tx.id,
        "client_id": tx.client["clientId"],
        "scopes": tx.scopes,
        "status": tx.status,
        "failure_reason": tx.failure_reason,
        "evidence": [
            {"type": item.credential_type, "vct": item.payload.get("vct"), "issuer": item.payload.get("iss")}
            for item in tx.presented.values()
        ],
    }
    if representation:
        entry["representation"] = {k: representation.get(k) for k in ("result", "reasons", "trust")}
    config.AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.AUDIT_LOG_FILE.open("a") as audit:
        audit.write(json.dumps(entry) + "\n")

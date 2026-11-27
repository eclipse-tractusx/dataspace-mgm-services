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
"""Pages of a transaction (C5-M1 6.6, 7.3)."""

import json
from html import escape

from common.web import THEMES, page, qr
from connector import config
from connector.transactions import Step, Transaction

TEXT = {
    "title": "Identify with your wallet",
    "tagline": "verification of credentials",
    "asks": "{client} wants to check:",
    "person_step": "EUDI Wallet",
    "company_step": "Business Wallet",
    "pid": "person identification data (PID) from your EUDI Wallet",
    "mandate": "mandate from your EUDI Wallet",
    "lpid": "company identification (LPID) from the company's Business Wallet",
    "scan": "Scan the QR code with your EUDI Wallet, or open it on this device:",
    "open_wallet": "Open in wallet",
    "bw_intro": "Now open your company's Business Wallet. Enter its wallet address once; this browser remembers it.",
    "bw_address": "Wallet address of the Business Wallet",
    "open_bw": "Open in Business Wallet",
    "copy_intro": "Or copy this link and paste it into the Business Wallet:",
    "copy": "Copy link",
    "waiting": "This page continues as soon as the wallet has answered.",
    "checked_by": "The EBW-Connector checks the credentials on behalf of {client}.",
    "done_title": "Step done",
    "done": "The wallet has answered. Please continue on your other device.",
    "error_title": "Invalid request",
}

POLL = """<script>
const seen = %s;
setInterval(async () => {
  try {
    const response = await fetch("/transactions/%s/status");
    if (!response.ok) return;
    const now = await response.json();
    if (now.status !== seen.status || now.step !== seen.step) location.reload();
  } catch (e) {}
}, 2000);
</script>"""

BUSINESS_WALLET = """<script>
const storageKey = "ebw-business-wallet-address";
const input = document.getElementById("bw-address");
try { input.value = localStorage.getItem(storageKey) || ""; } catch (e) {}
function openBusinessWallet() {
  const address = input.value.trim();
  if (!address) { input.focus(); return; }
  try { localStorage.setItem(storageKey, address); } catch (e) {}
  location.href = address + (address.includes("?") ? "&" : "?") + %s;
}
function copyRequest() { navigator.clipboard.writeText(document.getElementById("request-link").textContent); }
</script>"""


OWN_LOOK = {"brand": "EBW-Connector", "theme": "connector", "tagline": TEXT["tagline"]}


def look_of(client: dict) -> dict:
    """Brand, theme and tagline of the transaction page for a client: those of its `page` (6.8), so that a person
    sees which service they are signing in to. Without `page`, or with a theme this stack does not have, the look
    of the EBW-Connector itself."""
    wanted = client.get("page")
    if not isinstance(wanted, dict) or wanted.get("theme") not in THEMES or wanted["theme"] == OWN_LOOK["theme"]:
        return OWN_LOOK
    brand = str(wanted.get("brand") or client.get("name") or client["clientId"])
    return {"brand": brand, "theme": wanted["theme"], "tagline": str(wanted.get("tagline") or ""), "home": "#"}


def _wallet_link(step: Step) -> str:
    return f"{config.WALLET_URL_SCHEME}?{step.link_params}"


def transaction_page(tx: Transaction) -> str:
    t = TEXT
    step = tx.step
    requested = "".join(f"<li>{escape(t[cid])}</li>" for s in tx.steps for cid in s.credential_ids)
    progress = "".join(
        f'<span class="{"done" if s.status == "VERIFIED" else "current" if s is step else ""}">'
        f'{i + 1}. {escape(t[s.name + "_step"])}</span>'
        for i, s in enumerate(tx.steps)
    )
    body = f"<p>{escape(t['asks'].format(client=tx.client.get('name', tx.client['clientId'])))}</p><ul>{requested}</ul>"
    if len(tx.steps) > 1:
        body += f'<div class="steps">{progress}</div>'
    if step.name == "person":
        link = _wallet_link(step)
        body += (
            f'<div class="box"><h2>{escape(t["person_step"])}</h2><p>{escape(t["scan"])}</p>'
            + qr(link)
            + f'<p><a class="button" id="wallet-link" href="{escape(link)}">{escape(t["open_wallet"])}</a></p></div>'
        )
    else:
        body += (
            f'<div class="box"><h2>{escape(t["company_step"])}</h2><p>{escape(t["bw_intro"])}</p>'
            f'<label for="bw-address">{escape(t["bw_address"])}</label>'
            '<input id="bw-address" type="url" placeholder="https://…/present">'
            f'<p><button onclick="openBusinessWallet()">{escape(t["open_bw"])}</button></p>'
            f'<p class="muted">{escape(t["copy_intro"])}</p><pre id="request-link">{escape(_wallet_link(step))}</pre>'
            f'<p><button class="secondary" onclick="copyRequest()">{escape(t["copy"])}</button></p></div>'
            + BUSINESS_WALLET % json.dumps(step.link_params)
        )
    body += f'<p class="muted">{escape(t["waiting"])}</p>'
    look = look_of(tx.client)
    if look is not OWN_LOOK:
        # The page looks like the client, so it says who runs it.
        body += f'<p class="muted" id="checked-by">{escape(t["checked_by"].format(client=look["brand"]))}</p>'
    body += POLL % (json.dumps({"status": tx.status, "step": step.name}), tx.id)
    return page(t["title"], body, **look)


def done_page() -> str:
    return page(TEXT["done_title"], f"<p>{escape(TEXT['done'])}</p>", **OWN_LOOK)


def error_page(message: str) -> str:
    return page(TEXT["error_title"], f'<p class="fail">{escape(message)}</p>', **OWN_LOOK)

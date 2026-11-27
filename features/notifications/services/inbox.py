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
"""The own inbox of a person (README 4, 6.3, 7.2, 7.3).

Personal notifications with the caller's `sub`, plus staff notifications whose permission is in
the token; hidden ones are left out. Notifications are shown as the schema `Notification` with
`read` for the caller. A notification outside the own inbox gives 404 `not-found`.
"""
from __future__ import annotations

from collections.abc import Callable

from features.notifications.managers import store
from features.notifications.models import errors
from features.notifications.models.notification import Notification
from features.notifications.services import marks
from portal_common import sse

# openapi `Notification`, apart from `read`, which is per person
FIELDS = tuple(f.alias for name, f in Notification.model_fields.items() if name != "read")


def view(n: dict, state: dict) -> dict:
    """Schema `Notification` with `read` from the person's `notification_state` row (README 7.3)."""
    return {f: n[f] for f in FIELDS} | {"read": marks.read_in(state)}


def own(claims: dict) -> list[dict]:
    """README 4 and 7.1: the caller's notifications as `Notification` views, hidden ones left out; two queries,
    however large the inbox."""
    with store.LOCK:
        states = store.states(claims.get("sub"))
        return [view(n, state) for n in store.inbox(claims)
                if not marks.hidden_in(state := states.get(n["notificationId"], {}))]


def find(notification_id: str, claims: dict) -> dict:
    """The stored notification if it is in the caller's inbox, else Problem 404 `not-found` (README 7)."""
    n = store.find(notification_id)
    if n is not None and store.visible_to(n, claims):
        return n
    raise errors.not_found()


def get(notification_id: str, claims: dict) -> dict:
    """README 7.3: one notification of the own inbox with `read` for the caller."""
    n = find(notification_id, claims)
    return view(n, store.state_of(notification_id, claims.get("sub")))


def count(claims: dict) -> dict:
    """README 7.2: counters of the own inbox (hidden ones left out)."""
    items = own(claims)
    return {"total": len(items),
            "unread": sum(not v["read"] for v in items),
            "openTasks": sum(marks.is_open_task(v) for v in items),
            "unreadInfo": sum(v["topic"] == "INFO" and not v["read"] for v in items)}


def events() -> sse.Broker:
    """README 7.6: the broker of the stream events of every inbox (`managers.store.BROKER`)."""
    return store.BROKER


def stream_filter(claims: dict) -> Callable[[dict], bool]:
    """README 7.6: which stream events the caller sees, by the `meta` of the event (as `visible_to`)."""
    return lambda meta: store.stream_visible(meta, claims)

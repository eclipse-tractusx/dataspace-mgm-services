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
"""Public interface of C11-M1.

The spec has no steps or queries for C11-M1 (README 8 and 9); any other call gets the scaffold fallback. The
functions below are the operations of the own inbox (README 7) that the controllers call, so the HTTP layer
stays a thin wrapper and the same operations can be called in-process.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from features.notifications.models import MODULE
from features.notifications.services import inbox, listing, marks
from portal_common import sse, standin
from portal_common.models import Page

__all__ = ["MODULE", "count_notifications", "get_notification", "hide_notification", "list_notifications",
           "mark_read", "mark_unread", "notification_events", "notification_stream_filter"]

__getattr__ = standin.missing_interface(MODULE)   # README 8 and 9: none; any call gets the scaffold fallback


def list_notifications(claims: dict, *, topic: str | None = None, ntype: str | None = None,
                       read: bool | None = None, done: bool | None = None, created_since: dt.datetime | None = None,
                       newest_first: bool = True, page: int = 0, size: int = 20) -> Page[dict]:
    """README 7.1: one page of the own inbox, filtered and sorted by `createdAt`."""
    filters = listing.Filters(topic, ntype, read, done, created_since)
    return listing.list_page(inbox.own(claims), filters, newest_first=newest_first, page=page, size=size)


def count_notifications(claims: dict) -> dict:
    """README 7.2: counters of the own inbox (hidden ones left out)."""
    return inbox.count(claims)


def get_notification(notification_id: str, claims: dict) -> dict:
    """README 7.3: one notification of the own inbox with `read` for the caller."""
    return inbox.get(notification_id, claims)


def mark_read(notification_id: str, claims: dict) -> None:
    """README 7.4: set `read_at` for the caller; idempotent, the first time is kept."""
    marks.mark_read(inbox.find(notification_id, claims), claims.get("sub"))


def mark_unread(notification_id: str, claims: dict) -> None:
    """README 7.4: remove `read_at` for the caller; idempotent."""
    marks.mark_unread(inbox.find(notification_id, claims), claims.get("sub"))


def hide_notification(notification_id: str, claims: dict) -> None:
    """README 7.5: hide for the caller; an open task gives 409 `task-open`; idempotent."""
    marks.hide(inbox.find(notification_id, claims), claims.get("sub"))


def notification_events() -> sse.Broker:
    """README 7.6: the broker of the stream events of every inbox."""
    return inbox.events()


def notification_stream_filter(claims: dict) -> Callable[[dict], bool]:
    """README 7.6: which stream events the caller sees."""
    return inbox.stream_filter(claims)

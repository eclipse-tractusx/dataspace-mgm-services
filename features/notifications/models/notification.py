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
"""The models of C11-M1 (openapi.yaml `components/schemas`): JSON in camelCase, as in the spec.

Times stay ISO 8601 strings as the store keeps them (FRAMEWORK 4.1), so the wire format does not change.
`companyId` and `subjectId` stay plain strings: they are copied from the event, which this module does not own.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from portal_common.models import ApiModel, Page, Uuid

Topic = Literal["INFO", "ACTION"]
"""`INFO` for information, `ACTION` for a task (README 2)."""

Sort = Literal["createdAt.desc", "createdAt.asc"]
"""Sort order of the list (README 7.1)."""


class NotificationType(StrEnum):
    """The `type` of a notification, one per rule (README 6.2)."""

    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    REVIEW_CASE_OPENED = "REVIEW_CASE_OPENED"
    APPLICATION_DECLINED = "APPLICATION_DECLINED"
    APPLICATION_COMPLETED = "APPLICATION_COMPLETED"
    CHANGE_REQUEST_OPENED = "CHANGE_REQUEST_OPENED"
    OFFER_REVIEW_REQUESTED = "OFFER_REVIEW_REQUESTED"
    OFFER_APPROVED = "OFFER_APPROVED"
    OFFER_DECLINED = "OFFER_DECLINED"
    SUBSCRIPTION_REQUESTED = "SUBSCRIPTION_REQUESTED"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED"
    SUBSCRIPTION_DECLINED = "SUBSCRIPTION_DECLINED"
    SUBSCRIPTION_URL_CHANGED = "SUBSCRIPTION_URL_CHANGED"
    APP_ROLES_ADDED = "APP_ROLES_ADDED"
    TECHNICAL_USER_WALLET_READY = "TECHNICAL_USER_WALLET_READY"
    TECHNICAL_USER_WALLET_FAILED = "TECHNICAL_USER_WALLET_FAILED"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"
    CONNECTOR_REGISTERED = "CONNECTOR_REGISTERED"
    PROCESS_STEP_FAILED = "PROCESS_STEP_FAILED"


class NotificationFields(ApiModel):
    """The fields of a notification that every reader sees (openapi `Notification` without `read`)."""

    notification_id: Uuid
    type: NotificationType
    topic: Topic
    company_id: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    content: dict[str, Any]
    for_staff: bool
    done: bool | None = None   # tasks only
    created_at: str
    done_at: str | None = None


class Notification(NotificationFields):
    """One notification of the own inbox with `read` for the caller (README 7.3)."""

    read: bool


class StoredNotification(NotificationFields):
    """A notification as the store keeps it (README 5 `notification`): also its rule, source event and receiver,
    a person (`receiverSub`) or a permission (`receiverPermission`)."""

    source_event_id: str | None = None
    rule: str
    receiver_sub: str | None = None
    receiver_permission: str | None = None


NotificationPage = Page[Notification]
"""README 7.1: one page of the own inbox."""


class NotificationCount(ApiModel):
    """README 7.2: counters of the own inbox, hidden notifications left out."""

    total: int
    unread: int
    open_tasks: int
    unread_info: int


class NotificationCreated(ApiModel):
    """`data` of the stream event `notification-created` (README 7.6): IDs, type and state, no `content`."""

    notification_id: Uuid
    type: NotificationType
    topic: Topic
    for_staff: bool
    done: bool | None = None   # tasks only; `true` if the task was created done (README 6.2)
    created_at: str


class NotificationDone(ApiModel):
    """`data` of the stream event `notification-done` (README 7.6)."""

    notification_id: Uuid
    done_at: str

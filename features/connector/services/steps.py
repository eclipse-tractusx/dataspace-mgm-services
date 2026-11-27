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
"""The steps of the connectors for Process Orchestration (README 8)."""
from __future__ import annotations

from portal_common.models import StepResult

from ..managers import connector_repository as repository
from ..managers.connector_repository import LOCK
from ..models import ACTIVE, INACTIVE, ConnectorIds, DeactivateSubscriptionConnectorsInput, UnlinkTechnicalUserInput
from ..models.errors import parse
from .common import canonical, publish_deactivated


def deactivate_subscription_connectors(
        input: DeactivateSubscriptionConnectorsInput | dict) -> StepResult[ConnectorIds]:
    """8.1: the connector of an ended or declined subscription becomes INACTIVE, without technical user.
    Also clears a link that an INACTIVE connector still holds (deleted while the subscription was
    PENDING, README 7.6). `ConnectorDeactivated` only for a real change of status, so a repetition
    publishes nothing and answers DONE with an empty list."""
    request = parse(DeactivateSubscriptionConnectorsInput, input, retryable=False)
    sub_id = canonical(request.offer_subscription_id)
    changed = []
    with LOCK:
        repository.mark_subscription_ended(sub_id)   # also without connectors, so a later registration is refused
        for c in repository.find(offer_subscription_id=sub_id):
            if c.status == INACTIVE and c.technical_user_id is None:
                continue
            was_active = c.status == ACTIVE
            c = repository.update(c.connector_id, status=INACTIVE, technical_user_id=None)
            repository.write_audit("deactivate-subscription-connectors", c.connector_id)
            if was_active:
                publish_deactivated(c)
            changed.append(c.connector_id)
    return StepResult[ConnectorIds].done(request, ConnectorIds(connector_ids=changed))


def unlink_technical_user(input: UnlinkTechnicalUserInput | dict) -> StepResult[ConnectorIds]:
    """8.2: removes the deleted technical user from the connector that uses it; the connector keeps its status."""
    request = parse(UnlinkTechnicalUserInput, input, retryable=False)
    tu_id = canonical(request.technical_user_id)
    changed = []
    with LOCK:
        repository.mark_technical_user_deleted(tu_id)   # also without connectors, so a later registration is refused
        for c in repository.find(technical_user_id=tu_id):
            repository.update(c.connector_id, technical_user_id=None)
            repository.write_audit("unlink-technical-user", c.connector_id)
            changed.append(c.connector_id)
    return StepResult[ConnectorIds].done(request, ConnectorIds(connector_ids=changed))

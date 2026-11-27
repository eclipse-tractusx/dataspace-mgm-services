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
"""The query of the connectors for other modules (README 9)."""
from __future__ import annotations

from ..managers import connector_repository as repository
from ..models import ACTIVE, ConnectorRef
from ..models.errors import problem
from .common import canonical, is_uuid


def list_connectors_internal(*, technical_user_id: str | None = None) -> list[ConnectorRef]:
    """9.1: the ACTIVE connectors that use this technical user."""
    if technical_user_id is None or not is_uuid(technical_user_id):
        raise problem(400, "validation", detail="technicalUserId must be a UUID")
    rows = repository.find(technical_user_id=canonical(technical_user_id), status=ACTIVE)
    return [ConnectorRef.model_validate(row, from_attributes=True) for row in rows]

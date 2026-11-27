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
#  Assisted-By: GitHub Copilot (claude-opus-5-5)
#################################################################################
"""C2-M2 as one object: configuration, DAO service, internal services and service implementations, created at
first use and on `reset()`."""
from __future__ import annotations

import logging
import threading

from features.app_access.managers import database
from features.app_access.managers.config import Config
from features.app_access.managers.dao import sql_dao_service
from features.app_access.managers.gateways import CompanyProfileGatewayImpl, SubscriptionsGatewayImpl
from features.app_access.managers.iam import portal_iam

from .app_client_service_impl import AppClientServiceImpl
from .company_users_steps_impl import CompanyUsersStepsImpl
from .context import Context
from .invitation_cleanup_job_impl import InvitationCleanupJobImpl
from .invitation_service_impl import InvitationServiceImpl
from .user_service_impl import UserServiceImpl

log = logging.getLogger(__name__)


class C2M2Module:
    def __init__(self, config: Config | None = None) -> None:
        config = config or Config()
        database.create_schema()
        self.ctx = Context(config, portal_iam(config), sql_dao_service(), SubscriptionsGatewayImpl(),
                           CompanyProfileGatewayImpl())
        self.apps = AppClientServiceImpl(self.ctx)
        self.users = UserServiceImpl(self.ctx, self.apps)
        self.company_steps = CompanyUsersStepsImpl(self.ctx, self.users)
        self.invitations = InvitationServiceImpl(self.ctx, self.users)
        self.cleanup = InvitationCleanupJobImpl(self.invitations.expire_overdue)

    def on_startup(self) -> None:
        self.invitations.bootstrap()
        self.cleanup.start()

    def close(self) -> None:
        self.cleanup.stop()


_lock = threading.Lock()
_current: C2M2Module | None = None


def current() -> C2M2Module:
    global _current
    with _lock:
        if _current is None:
            _current = C2M2Module()
        return _current


def reset() -> None:
    """Fresh data and configuration read again from the environment (README 4)."""
    global _current
    with _lock:
        if _current is not None:
            _current.close()
        _current = None
        database.reset_schema()


def on_startup() -> None:
    """Bootstrap and invitation cleanup at the start of a runtime; both only with a database URL (README 4),
    otherwise the data lives in the private in-memory database and starts empty."""
    if not Config().from_properties("database.url"):
        log.warning("C2-M2 has no database URL (APP_ACCESS_DATABASE_URL, C2_M2_DATABASE_URL or DATABASE_URL): "
                    "bootstrap and invitation cleanup skipped")
        return
    current().on_startup()

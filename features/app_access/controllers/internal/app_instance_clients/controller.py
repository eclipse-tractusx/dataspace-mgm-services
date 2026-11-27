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
#  Assisted-By: GitHub Copilot
#################################################################################
"""Instance clients of apps for other modules (README 9.2, 9.3), `query_c2_m2`. Queries over HTTP give the same
answer as the in-process interface, which keeps the contract's parameter names (call convention)."""
from __future__ import annotations

from fastapi import Query

from features.app_access import interface
from portal_common.routing import Controller, Permission

controller = Controller("App Access: Queries")


@controller.get("", operation_id="listAppInstanceClients", summary="Instance clients by app, subscription or customer")
def list_app_instance_clients(appId: str | None = None, offerSubscriptionId: str | None = None,
                              customerCompanyId: str | None = None, instanceKind: str | None = None,
                              status: list[str] | None = Query(None, description="May be given several times."),
                              _: dict = Permission) -> list[interface.Json]:
    return interface.list_app_instance_clients(appId=appId, offerSubscriptionId=offerSubscriptionId,
                                               customerCompanyId=customerCompanyId, instanceKind=instanceKind,
                                               status=status)


@controller.get("/{id}", operation_id="getAppInstanceClient", summary="One instance client")
def get_app_instance_client(id: str, _: dict = Permission) -> interface.Json:  # noqa: A002 - openapi name
    return interface.get_app_instance_client(id=id)

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
#  SPDX-License-Identifier: Apache-2.0
#################################################################################
"""In-memory Portal IAM adapter bridging to `tools/test_iam.py` when `IAM_URL` is empty."""
from __future__ import annotations

from features.app_access.managers.config import Config
from features.app_access.managers.ports import PortalIam
from tools import test_iam


class TestIamPortalIamAdapter(PortalIam):
    """In-memory Portal IAM adapter that delegates to `tools.test_iam.iam()`."""

    __test__ = False
    CORE_UUID = "portal-core-uuid"

    def __init__(self, config: Config) -> None:
        self.config = config
        self._clients: dict[str, dict] = {
            self.CORE_UUID: {
                "id": self.CORE_UUID,
                "clientId": config.from_properties("portal.core.client.id") or "portal-core",
            }
        }
        self._app_roles: dict[str, list[dict]] = {}

    def _iam(self) -> test_iam.IAM:
        return test_iam.iam()

    # -- clients -------------------------------------------------------------------------------
    def find_client(self, client_id: str) -> dict | None:
        for c in self._clients.values():
            if c.get("clientId") == client_id:
                return dict(c)
        return {"id": client_id, "clientId": client_id}

    def create_client(self, representation: dict) -> str:
        cid = representation.get("clientId") or representation.get("id") or "client-uuid"
        rep = dict(representation, id=cid)
        self._clients[cid] = rep
        return cid

    def get_client(self, uuid: str) -> dict:
        return dict(self._clients.get(uuid, {"id": uuid, "clientId": uuid}))

    def update_client(self, uuid: str, representation: dict) -> None:
        if uuid in self._clients:
            self._clients[uuid].update(representation)
        else:
            self._clients[uuid] = dict(representation, id=uuid)

    def protocol_mappers(self, uuid: str) -> list[dict]:
        return []

    def create_protocol_mapper(self, uuid: str, mapper: dict) -> None:
        pass

    # -- client roles --------------------------------------------------------------------------
    def client_roles(self, uuid: str) -> list[dict]:
        portal = [{"id": f"role-{name}", "name": name} for name in self._iam().portal_roles]
        return portal + list(self._app_roles.get(uuid, []))

    def client_role(self, uuid: str, name: str) -> dict | None:
        return {"id": f"role-{name}", "name": name}

    def create_client_role(self, uuid: str, name: str, description: str | None) -> None:
        self._app_roles.setdefault(uuid, []).append({"id": f"role-{name}", "name": name, "description": description})

    def update_client_role(self, uuid: str, name: str, representation: dict) -> None:
        pass

    def users_with_client_role(self, uuid: str, name: str) -> list[dict]:
        uids = self._iam().users_with_portal_role(name)
        return [{"id": uid} for uid in uids]

    # -- accounts ------------------------------------------------------------------------------
    def get_user(self, user_id: str) -> dict | None:
        u = self._iam().users.get(user_id)
        if not u:
            return None
        company_id = u.get("companyId")
        bpn = u.get("bpn")
        attrs = {}
        if company_id:
            attrs["company_id"] = [company_id]
        if bpn:
            attrs["bpn"] = [bpn]
        return {
            "id": user_id,
            "firstName": u.get("givenName") or "",
            "lastName": u.get("familyName") or "",
            "email": f"{u.get('givenName', 'user').lower()}@example.com",
            "enabled": True,
            "attributes": attrs,
        }

    def update_user(self, user_id: str, representation: dict) -> None:
        attrs = representation.get("attributes") or {}
        company_id = attrs.get("company_id", [None])[0] if attrs.get("company_id") else None
        bpn = attrs.get("bpn", [None])[0] if attrs.get("bpn") else None
        self._iam().bind(user_id, company_id, bpn)

    def logout_user(self, user_id: str) -> None:
        pass

    def role_mappings(self, user_id: str) -> dict | None:
        u = self._iam().users.get(user_id)
        if not u:
            return None
        roles = [{"id": f"role-{r}", "name": r} for r in u.get("roles", [])]
        entry = {
            "id": self.CORE_UUID,
            "client": "portal-core",
            "mappings": roles,
        }
        return {
            "clientMappings": {
                self.CORE_UUID: entry,
                "portal-core": entry,
            }
        }

    def client_role_mappings(self, user_id: str, uuid: str) -> list[dict]:
        u = self._iam().users.get(user_id)
        if not u:
            return []
        return [{"id": f"role-{r}", "name": r} for r in u.get("roles", [])]

    def add_client_role_mappings(self, user_id: str, uuid: str, roles: list[dict]) -> None:
        role_names = [r["name"] for r in roles if "name" in r]
        self._iam().add_portal_roles(user_id, role_names)

    def remove_client_role_mappings(self, user_id: str, uuid: str, roles: list[dict]) -> None:
        role_names = [r["name"] for r in roles if "name" in r]
        self._iam().remove_portal_roles(user_id, role_names)

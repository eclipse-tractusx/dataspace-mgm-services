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
"""Operations of people on the connector register (README 7) with the checks of README 6.2 and the
calls to the neighbours C3-M1, C2-M3 and C10-M1 (README 11, `managers/neighbour_client.py`). No token checks
here; the controllers pass the calling company and person and the validated body."""
from __future__ import annotations

import ipaddress
import re
import uuid
from urllib.parse import urlparse

from portal_common import events
from portal_common.models import Page

from ..managers import config, neighbour_client
from ..managers import connector_repository as repository
from ..managers.connector_repository import LOCK, now
from ..models import (
    ACTIVE,
    COMPANY_CONNECTOR,
    CONNECTOR_AS_A_SERVICE,
    INACTIVE,
    MODULE,
    Connector,
    ConnectorAsAServiceInput,
    ConnectorInput,
    EndpointChange,
)
from ..models.errors import problem
from ..models.tables import ConnectorRow
from .common import canonical, is_uuid, publish_deactivated

# ---------------------------------------------------------------- checks (README 6.2)
_LABEL = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")
_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")


def _valid_host(host: str) -> bool:
    """IP address, or DNS name of letters, digits and hyphens (RFC 1123), as the CSP discovery stores it."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    labels = host.rstrip(".").split(".")
    return (len(host) <= 253 and all(_LABEL.fullmatch(label) for label in labels)
            and not all(label.isdigit() for label in labels))


def _endpoint_error(endpoint: str) -> str | None:
    """None for a usable HTTPS endpoint, otherwise the message (never echoing the value, FRAMEWORK 4.6)."""
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > 2000 or not endpoint.isascii() \
            or any(ch.isspace() or ord(ch) < 32 or ch in "\\\x7f" for ch in endpoint) or _PERCENT.search(endpoint):
        return "HTTPS URL"
    try:
        url = urlparse(endpoint)
        port = url.port   # raises ValueError for an invalid port
    except ValueError:
        return "HTTPS URL"
    if url.username is not None or url.password is not None:   # no credentials in data or events
        return "must not contain user information"
    if url.scheme != "https" or not url.hostname or not _valid_host(url.hostname) or url.fragment \
            or port == 0 or endpoint.endswith("#"):
        return "HTTPS URL"
    return None


def _check_endpoint_and_location(endpoint: str, location: str | None = None) -> None:
    """The checks beyond the shape of the body: a usable HTTPS endpoint and a country of the reference data."""
    errors = []
    if (message := _endpoint_error(endpoint)) is not None:
        errors.append({"field": "endpoint", "message": message})
    countries = config.known_countries() if location is not None else None
    if countries is not None and location not in countries:
        errors.append({"field": "location", "message": "unknown country code"})
    if errors:
        raise problem(400, "validation", errors=errors)


def _check_duplicate(name: str, endpoint: str, ignore: str | None = None) -> None:
    if repository.live_exists(name=name, endpoint=endpoint, ignore=ignore):
        raise problem(409, "duplicate", detail="a connector with this name and endpoint exists")


def _check_technical_user(tu_id: str | None, host: str, sub_id: str | None) -> None:
    if not tu_id:
        return
    linked = repository.live_exists(technical_user_id=tu_id)
    if linked or not neighbour_client.technical_user_usable(tu_id, host, sub_id):
        raise problem(409, "technical-user-not-usable")


def _check_host_active(host: str) -> None:
    if neighbour_client.company_status(host) != ACTIVE:
        raise problem(409, "company-not-active")


def _own_company(company_id: str | None) -> str:
    if not company_id:
        raise problem(403, "forbidden", detail="the token has no company_id")
    return company_id


def _visible(connector_id: str, company_id: str) -> ConnectorRow:
    c = repository.get(canonical(connector_id)) if is_uuid(connector_id) else None
    if not c or company_id not in (c.provider_company_id, c.host_company_id):
        raise problem(404, "not-found")
    return c


def _view(c: ConnectorRow) -> Connector:
    return Connector.model_validate(c, from_attributes=True)


# ---------------------------------------------------------------- operations (README 7)
def _register(body: ConnectorInput, *, technical_user_id: str | None, ctype: str, provider: str, host: str,
              sub_id: str | None, sub: str | None) -> Connector:
    """The final uniqueness checks of README 5 and the insert as one unit under LOCK: of two concurrent
    requests that both passed the earlier checks, the second gets 409."""
    with LOCK:
        if sub_id and repository.subscription_ended(sub_id):
            raise problem(409, "invalid-state", detail="subscription ended or declined")
        if sub_id and repository.live_exists(offer_subscription_id=sub_id):
            raise problem(409, "subscription-linked")
        _check_duplicate(body.name, body.endpoint)
        if technical_user_id and repository.technical_user_deleted(technical_user_id):
            raise problem(409, "technical-user-not-usable", detail="technical user was deleted")
        if technical_user_id and repository.live_exists(technical_user_id=technical_user_id):
            raise problem(409, "technical-user-not-usable")
        c = repository.add(ConnectorRow(
            connector_id=str(uuid.uuid4()), name=body.name, endpoint=body.endpoint, location=body.location,
            type=ctype, status=ACTIVE, provider_company_id=provider, host_company_id=host,
            technical_user_id=technical_user_id, offer_subscription_id=sub_id, created_at=now()))
        repository.write_audit("register-connector", c.connector_id, sub, provider)
        events.publish(MODULE, "ConnectorRegistered", {
            "connectorId": c.connector_id, "companyId": host, "providerCompanyId": provider, "type": ctype,
            "endpoint": c.endpoint, "location": c.location})
        return _view(c)


def list_connectors(company_id: str | None, *, role: str | None = None, type: str | None = None,
                    status: str | None = None, page: int = 0, size: int = 20) -> Page[Connector]:
    """7.1"""
    rows, total = repository.page_of_company(_own_company(company_id), role=role, type=type, status=status,
                                             page=page, size=size)
    return Page[Connector](items=[_view(c) for c in rows], page=page, size=size, total=total)


def register_connector(company_id: str | None, sub: str | None, body: ConnectorInput) -> Connector:
    """7.2: company connector of the own company."""
    own = _own_company(company_id)
    _check_endpoint_and_location(body.endpoint, body.location)
    tu_id = canonical(body.technical_user_id) if body.technical_user_id else None
    _check_host_active(own)
    _check_duplicate(body.name, body.endpoint)
    _check_technical_user(tu_id, own, None)
    return _register(body, technical_user_id=tu_id, ctype=COMPANY_CONNECTOR, provider=own, host=own, sub_id=None,
                     sub=sub)


def register_connector_as_a_service(company_id: str | None, sub: str | None,
                                    body: ConnectorAsAServiceInput) -> Connector:
    """7.3: provider = own company, host = customer of the subscription of an own offer."""
    own = _own_company(company_id)
    _check_endpoint_and_location(body.endpoint, body.location)
    sub_id = canonical(body.offer_subscription_id)
    tu_id = canonical(body.technical_user_id) if body.technical_user_id else None
    s = neighbour_client.subscription(sub_id)
    if not s or s.get("providerCompanyId") != own:
        raise problem(404, "not-found", detail="subscription unknown or not of an own offer")
    if s.get("status") not in ("PENDING", "ACTIVE"):
        raise problem(409, "invalid-state", detail=f"subscription is {s.get('status')}")
    if repository.live_exists(offer_subscription_id=sub_id):
        raise problem(409, "subscription-linked")
    host = s["customerCompanyId"]
    _check_host_active(host)
    _check_duplicate(body.name, body.endpoint)
    _check_technical_user(tu_id, host, sub_id)
    return _register(body, technical_user_id=tu_id, ctype=CONNECTOR_AS_A_SERVICE, provider=own, host=host,
                     sub_id=sub_id, sub=sub)


def get_connector(company_id: str | None, connector_id: str) -> Connector:
    """7.4"""
    return _view(_visible(connector_id, _own_company(company_id)))


def change_endpoint(company_id: str | None, sub: str | None, connector_id: str, body: EndpointChange) -> Connector:
    """7.5: only the provider company; same value = 200 without change. Under LOCK, so that its duplicate
    check and change do not interleave with other changes."""
    own = _own_company(company_id)
    with LOCK:
        c = _visible(connector_id, own)
        if c.provider_company_id != own:
            raise problem(403, "forbidden", detail="only the provider company changes the endpoint")
        if c.status == INACTIVE:
            raise problem(409, "invalid-state", detail="connector is INACTIVE")
        _check_endpoint_and_location(body.endpoint)
        if body.endpoint == c.endpoint:
            return _view(c)
        _check_duplicate(c.name, body.endpoint, ignore=c.connector_id)
        c = repository.update(c.connector_id, endpoint=body.endpoint)
        repository.write_audit("change-endpoint", c.connector_id, sub, own)
        events.publish(MODULE, "ConnectorEndpointChanged", {"connectorId": c.connector_id,
                                                            "companyId": c.host_company_id, "endpoint": c.endpoint})
        return _view(c)


def delete_connector(company_id: str | None, sub: str | None, connector_id: str) -> None:
    """7.6: with a linked subscription the connector becomes INACTIVE and keeps the link; otherwise removed.
    C10-M1 is asked outside LOCK (it may be slow); the change runs under LOCK on the current row."""
    own = _own_company(company_id)
    sub_id = _visible(connector_id, own).offer_subscription_id
    s = neighbour_client.subscription(sub_id) if sub_id else None
    with LOCK:
        c = _visible(connector_id, own)   # may have been deleted meanwhile: 404
        if c.offer_subscription_id:
            if s and s.get("status") == ACTIVE:
                raise problem(409, "subscription-active")
            if c.status != INACTIVE:
                c = repository.update(c.connector_id, status=INACTIVE)
                repository.write_audit("delete-connector", c.connector_id, sub, own)
                publish_deactivated(c)
            return
        repository.delete(c.connector_id)
        repository.write_audit("delete-connector", c.connector_id, sub, own)
        events.publish(MODULE, "ConnectorDeleted", {"connectorId": c.connector_id, "companyId": c.host_company_id})

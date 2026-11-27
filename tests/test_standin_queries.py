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
"""Queries that a module calls at a neighbour (section 11 of every README) exist in the neighbour's
stand-in and answer with the field names of the neighbour's openapi.yaml. A team that replaces one
stand-in must find every other one complete. Modules of a team are not checked here; their own
tests cover them."""
import importlib
import re

import pytest

from portal_common import events, layout, spec, standin
from scaffold import registry
from conftest import needs_admin_api
from test_demo_scenarios import installation

CALL = re.compile(r"`(GET|POST|PUT|PATCH|DELETE) (?:/api/([a-z0-9-]+))?(/internal/[^`?\s]*)")


def _module_of(base: str) -> str | None:
    """Module id for the base in a README path: `/api/c3-m1` (old) or `/api/company-profile` (FRAMEWORK 4.1, OP-55)."""
    if base in spec.modules():
        return base
    return next((m for m, ms in spec.modules().items() if ms.spec_path == f"/api/{base}"), None)


def neighbour_queries() -> dict[tuple[str, str], set[str]]:
    """(target module, function) -> calling modules, from the tables of README section 11."""
    out: dict[tuple[str, str], set[str]] = {}
    for caller, ms in spec.modules().items():
        sec = re.search(r"^## 11\..*?(?=^## 12\.|\Z)", spec.readme(ms.folder), re.S | re.M)
        for row in (sec.group(0) if sec else "").splitlines():
            for method, base, path in CALL.findall(row):
                target = _module_of(base) if base else None
                if not target:   # path without /api/<module>: the module whose spec has it, named in the row
                    found = [m for m in spec.modules() if spec.module(m).find(method, path)]
                    named = [m for m in found if m in row.lower()]
                    target = (named or found)[0] if len(named or found) == 1 else None
                assert target, f"{caller} section 11: {method} {path} matches no single module"
                op = spec.module(target).find(method, path)
                assert op and op.function_name, f"{caller} section 11: {method} /api/{target}{path} not in the spec"
                out.setdefault((target, op.function_name), set()).add(caller)
    return out


QUERIES = sorted(neighbour_queries())


def kit_owned(target: str) -> bool:
    """Stand-ins, provided modules and migrated features (whose interface keeps the stand-in fallback)."""
    return next(e.kind for e in registry.load() if e.id == target) in ("stand-in", "provided", "feature")


def test_section_11_is_parsed():
    assert ("c3-m1", "find_identifier_matches") in QUERIES and ("c1-m3", "get_review_status_by_application") in QUERIES
    assert ("c10-m1", "find_subscriptions") in QUERIES   # C2-M2 names it without /api/c10-m1


@pytest.mark.parametrize("target,function", QUERIES)
def test_standin_implements_every_query_its_neighbours_call(target, function):
    if not kit_owned(target):
        pytest.skip(f"{target} is a team module")
    iface = importlib.import_module(layout.interface_package(target))
    assert function in vars(iface), (f"stand-in {target} lacks {function} (called by "
                                     f"{sorted(neighbour_queries()[(target, function)])}); it would answer 501")


# ---------------------------------------------------------------- field names
def field_errors(ms: spec.ModuleSpec, schema: dict, value, where: str = "$") -> list[str]:
    """Field names of `value` against the response schema: no field the schema does not name,
    every required field present. Values themselves are not checked."""
    if value is None or not schema:
        return []
    for key in ("oneOf", "anyOf"):
        if key in schema:
            options = [field_errors(ms, s, value, where) for s in schema[key]
                       if ms.resolve(s).get("type") != "null"]
            return [] if any(not o for o in options) else min(options, key=len)
    schema = ms.resolve(schema)
    if isinstance(value, list):
        return [e for i, v in enumerate(value) for e in field_errors(ms, schema.get("items") or {}, v, f"{where}[{i}]")]
    if not isinstance(value, dict) or "properties" not in schema:
        return []
    props = schema["properties"]
    errors = [f"{where}.{k}: not in the spec" for k in value if k not in props]
    errors += [f"{where}.{k}: required, missing" for k in schema.get("required", []) if k not in value]
    return errors + [e for k, v in value.items() if k in props for e in field_errors(ms, props[k], v, f"{where}.{k}")]


def response_schema(target: str, function: str) -> tuple[spec.ModuleSpec, dict]:
    ms = spec.module(target)
    op = next(o for o in ms.operations if o.function_name == function)
    ok = ms.document["paths"][op.path][op.method.lower()]["responses"]["200"]
    return ms, ok["content"]["application/json"]["schema"]


def _params(ids: dict) -> dict[tuple[str, str], dict | None]:
    """Parameters per query after scenarios 1-3; None = not callable with the stand-in."""
    return {
        ("c1-m2", "get_application_internal"): {"applicationId": ids["applicationId"]},
        ("c1-m2", "list_applications_internal"): {"applicationId": [ids["applicationId"]]},
        ("c1-m2", "list_agreements_internal"): {},
        ("c1-m3", "get_review_status_by_application"): {"applicationId": ids["applicationId"]},
        ("c10-m1", "find_subscriptions"): {"customerCompanyId": ids["companyId"]},
        ("c10-m1", "get_subscription_internal"): {"offerSubscriptionId": ids["offerSubscriptionId"]},
        ("c12-m1", "find_processes_of_subject"): {"subjectType": "SUBSCRIPTION", "subjectId": ids["offerSubscriptionId"]},
        ("c2-m2", "list_app_roles"): {"appId": [ids["offerId"]]},
        ("c2-m2", "list_company_user_refs"): {"companyId": ids["companyId"]},
        ("c2-m2", "list_app_instance_clients"): {"offerSubscriptionId": ids["offerSubscriptionId"]},
        ("c2-m3", "check_technical_user"): {"id": ids["technicalUserId"]},
        ("c2-m3", "list_technical_roles"): {},
        ("c2-m3", "rotate_subscription_credentials"): {"id": ids["technicalUserId"],
                                                        "offerSubscriptionId": ids["offerSubscriptionId"]},
        ("c3-m1", "query_company"): {"companyId": ids["companyId"]},
        ("c3-m1", "query_companies"): {"bpn": [ids["bpn"]]},
        ("c3-m1", "find_identifier_matches"): {"identifiers": [{"type": "VAT_ID", "value": "DE123456789"}]},
        ("c3-m2", "find_companies"): {"ebwoid": "x", "legalName": "Beispiel Maschinenbau GmbH", "country": "DE"},
        ("c4-m2", "get_wallet_info"): {"companyId": ids["companyId"]},
        ("c4-m2", "get_holder_access"): None,   # route STUB has no holder access (C4-M1 11.2)
        ("c6-m1", "list_connectors_internal"): {"technicalUserId": ids["technicalUserId"]},
        ("c8-m1", "get_offer_internal"): {"offerId": ids["offerId"]},
    }


@needs_admin_api
def test_standin_queries_answer_with_the_field_names_of_the_spec(tmp_path, monkeypatch):
    with installation(tmp_path, monkeypatch) as t:
        assert t.ok, "scenarios 1-3 failed; see test_demo_scenarios"
        log = {e["type"]: e["data"] for e in events.RELAY.log}   # CloudEvents (FRAMEWORK 6)
        ids = {"applicationId": log["ApplicationSubmitted"]["applicationId"],
               "companyId": log["CompanyActivated"]["companyId"], "bpn": log["CompanyActivated"]["bpn"],
               "offerId": log["OfferApproved"]["offerId"],
               "offerSubscriptionId": log["SubscriptionRequested"]["offerSubscriptionId"],
               "technicalUserId": log["TechnicalUserCreated"]["technicalUserId"]}
        params, errors, checked = _params(ids), [], 0
        for target, function in QUERIES:
            assert (target, function) in params, f"add parameters for {target} {function} to this test"
            if params[(target, function)] is None or not kit_owned(target):
                continue
            answer = standin.interface_function(target, function)(**params[(target, function)])
            ms, schema = response_schema(target, function)
            errors += [f"{target} {function} {e}" for e in field_errors(ms, schema, answer)]
            checked += 1
    assert not errors, "\n".join(errors)
    # The more teams replace their stand-in, the fewer queries are left to check here.
    assert checked == sum(1 for q in QUERIES if params[q] is not None and kit_owned(q[0]))


def test_standin_router_custom_tags():
    r_default = standin.router("c1-m2")
    assert r_default.tags == ["c1-m2 (stand-in)"]
    r_custom = standin.router("c1-m2", tags=["c1-m2 Registration"])
    assert r_custom.tags == ["c1-m2 Registration"]


#!/usr/bin/env python3
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
"""Build the realm files of the test installation from realm-osp.json (C2-M5 14.1).

realm-osp.json stays the only source. This script replaces its placeholders with test values,
adds the test objects and writes one directory per variant:

    test/import/hackathon/  OSP A and OSP B, persons from testdata/ (FRAMEWORK 7a)
    test/import/test/       one installation for the tests of C2-M5: Erika and Max are bound

With --sign-in it builds one more variant, named after the value. It is the variant hackathon without the
stand-in TEST-EBW, with the sign-in methods of the value (iam/README.md "Sign-in methods"):

    test/import/wallet/     only the wallet: the Portal IAM redirects to the EBW-Connector (ebw/) at --ebw-connector-url
    test/import/both/       password or wallet: the sign-in page of the Portal IAM with a form and the button of the
                            EBW-Connector; the test persons have a password
    test/import/password/   only the password: the identity provider is disabled, no EBW-Connector is needed

For wallet and both, the clients the EBW-Connector has to know are written to test/import/<value>.ebw-clients.json.

Usage:  uv run python iam/test/build-test-realm.py [--jwks-base URL] [--csp-jwks-url URL] [--out DIR]
                                                   [--sign-in wallet|both|password] [--ebw-connector-url URL]
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

TEST = Path(__file__).resolve().parent
IAM = TEST.parent
ROOT = IAM.parent
sys.path.insert(0, str(ROOT))
from portal_common import spec  # noqa: E402

IAM_URL = "http://localhost:8080/auth"
STAND_IN = f"{IAM_URL}/realms/TEST-EBW"
COMMON = {
    "IAM_SSL_REQUIRED": "external",
    "IAM_ACCESS_TOKEN_LIFESPAN": "300",
    "IAM_SSO_IDLE_TIMEOUT": "1800",
    "IAM_SSO_MAX_LIFESPAN": "36000",
    "IAM_EVENTS_EXPIRATION": "7776000",
    "EBW_CONNECTOR_URL": STAND_IN,
}


def read_env():
    env = {}
    for line in (TEST / ".env.test").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            env[key] = value
    return env


def fill(text, values):
    for key, value in values.items():
        text = text.replace("${" + key + "}", value)
    return text


def stand_in_id(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"test-ebw:{key}"))


def stand_in_users():
    """Everybody in testdata/ can sign in at the stand-in; Nina has no account yet (first login, C2-M5 13 case 3)."""
    users = {"nina": {"key": "nina", "givenName": "Nina", "familyName": "Neu"}}
    for file in sorted((ROOT / "testdata").glob("persons-osp-*.json")):
        for person in json.loads(file.read_text(encoding="utf-8"))["persons"]:
            users[person["key"]] = person
    return users


def account(person, stand_ins, password=None):
    stand_in = stand_ins[person["key"]]
    uid = stand_in_id(person["key"])
    user = {
        "id": person["id"],
        "username": f"ebw.{uid}",
        "firstName": stand_in["givenName"],
        "lastName": stand_in["familyName"],
        "enabled": True,
        "federatedIdentities": [{"identityProvider": "ebw-connector", "userId": uid, "userName": person["key"]}],
        "clientRoles": {"portal-core": ["Applicant", *person.get("portalRoles", [])], **person.get("appRoles", {})},
    }
    if person.get("companyId"):
        user["attributes"] = {"company_id": [person["companyId"]], "bpn": [person["bpn"]]}
    if password:
        # Sign-in with a password at the Portal IAM itself: the name is the key of the person. The link to the
        # stand-in stays, because `tools.keycloak_admin.reset_realm` recognises the persons by it.
        user["username"] = person["key"]
        user["credentials"] = [{"type": "password", "value": password, "temporary": False}]
    return user


ONLY_FOR = {"read_wallet_holder_access": "svc-c4-m1", "rotate_subscription_credentials": "svc-c10-m1"}  # C2-M5 6.2


def service_accounts(realm, secret):
    """`svc-<module>` of every module of the spec and `svc-test-internal` get every step and query permission
    (C2-M5 14.2), as `tokens.service_token` expects; the permissions in ONLY_FOR only the account named there
    and `svc-test-internal`. `svc-c2-m2` and `svc-c2-m3` keep their rights on the Admin API."""
    names = [r["name"] for r in realm["roles"]["client"]["portal-core"]
             if r["name"].startswith(("execute_steps_", "query_")) or r["name"] in ("read_wallet_holder_access", "rotate_subscription_credentials")]
    by_folder_name = sorted(spec.modules(), key=lambda mid: mid.replace("-", "_"))  # order of the former folder names
    ids = [f"svc-{mid}" for mid in by_folder_name]
    clients = {c["clientId"]: c for c in realm["clients"]}
    users = {u["username"]: u for u in realm["users"]}
    for client_id in [*ids, "svc-test-internal"]:
        granted = [n for n in names if client_id in (ONLY_FOR.get(n, client_id), "svc-test-internal")]
        if client_id not in clients:
            realm["clients"].append({
                "clientId": client_id, "name": f"HTTP between modules (test): {client_id}", "enabled": True, "publicClient": False,
                "standardFlowEnabled": False, "implicitFlowEnabled": False, "directAccessGrantsEnabled": False, "serviceAccountsEnabled": True,
                "fullScopeAllowed": False, "protocol": "openid-connect", "clientAuthenticatorType": "client-secret", "secret": secret,
                "attributes": {"client_credentials.use_refresh_token": "false"},
                "defaultClientScopes": ["basic", "roles", "portal-core-audience"], "optionalClientScopes": [],
            })
            realm["users"].append({"username": f"service-account-{client_id}", "enabled": True, "serviceAccountClientId": client_id, "clientRoles": {"portal-core": granted}})
        else:
            clients[client_id]["defaultClientScopes"].append("portal-core-audience")
            users[f"service-account-{client_id}"]["clientRoles"]["portal-core"] = granted
        realm["clientScopeMappings"]["portal-core"].append({"client": client_id, "roles": granted})


def technical_user(realm, secret):
    realm["clients"].append({
        "clientId": "sa-test-u1", "name": "Technical user (test)", "enabled": True, "publicClient": False,
        "standardFlowEnabled": False, "implicitFlowEnabled": False, "directAccessGrantsEnabled": False, "serviceAccountsEnabled": True,
        "fullScopeAllowed": False, "protocol": "openid-connect", "clientAuthenticatorType": "client-secret", "secret": secret,
        "attributes": {"client_credentials.use_refresh_token": "false"},
        "defaultClientScopes": ["basic", "roles", "catena", "technical-roles"], "optionalClientScopes": [],
    })
    realm["users"].append({
        "username": "service-account-sa-test-u1", "enabled": True, "serviceAccountClientId": "sa-test-u1",
        "attributes": {"company_id": ["c0000001-0000-4000-8000-000000000001"], "bpn": ["BPNLIUK2REMLK3F4"]},
        "clientRoles": {"technical_roles_management": ["Dataspace Discovery"]},
    })


def app_test(realm):
    def role(name, en, de):
        return {"name": name, "description": en, "composite": False, "clientRole": True, "attributes": {"description.de": [de], "description.en": [en]}}
    realm["clients"].append({
        "clientId": "app-test", "name": "Test app", "enabled": True, "publicClient": True,
        "standardFlowEnabled": True, "implicitFlowEnabled": False, "directAccessGrantsEnabled": False, "serviceAccountsEnabled": False,
        "fullScopeAllowed": False, "protocol": "openid-connect", "redirectUris": ["http://localhost:8081/*"], "webOrigins": ["+"],
        "attributes": {"pkce.code.challenge.method": "S256"},
        "defaultClientScopes": ["basic", "roles", "web-origins", "acr", "catena"], "optionalClientScopes": [],
        "protocolMappers": [{"name": "app-test-audience", "protocol": "openid-connect", "protocolMapper": "oidc-audience-mapper", "consentRequired": False,
                             "config": {"included.client.audience": "app-test", "access.token.claim": "true", "id.token.claim": "false", "introspection.token.claim": "true"}}],
    })
    realm["roles"]["client"]["app-test"] = [role("Viewer", "May read data", "Darf Daten lesen"), role("Editor", "May change data", "Darf Daten ändern")]


def stand_in_client(client_id, name, realm_name, auth="client-jwt", secret=None, mappers=None):
    client = {
        "clientId": client_id, "name": name, "enabled": True, "publicClient": False, "protocol": "openid-connect",
        "standardFlowEnabled": True, "implicitFlowEnabled": False, "directAccessGrantsEnabled": False, "serviceAccountsEnabled": False,
        "clientAuthenticatorType": auth, "redirectUris": [f"{IAM_URL}/realms/{realm_name}/broker/ebw-connector/endpoint"],
        "attributes": {"pkce.code.challenge.method": "S256", "use.jwks.url": "true", "jwks.url": f"{IAM_URL}/realms/{realm_name}/protocol/openid-connect/certs", "token.endpoint.auth.signing.alg": "ES256"},
        "defaultClientScopes": ["profile"], "optionalClientScopes": [], "protocolMappers": mappers or [],
    }
    if secret:
        client["secret"] = secret
        client["attributes"] = {"pkce.code.challenge.method": "S256"}
    return client


def hardcoded(claim, value):
    return {"name": claim, "protocol": "openid-connect", "protocolMapper": "oidc-hardcoded-claim-mapper", "consentRequired": False,
            "config": {"claim.name": claim, "claim.value": value, "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "false"}}


def stand_in_realm(installations, stand_ins, env, extras):
    clients = []
    for item in installations:
        values = item["values"]
        clients.append(stand_in_client(values["EBW_CONNECTOR_CLIENT_ID"], f"Portal IAM of {values['IAM_REALM']}", values["IAM_REALM"]))
    if extras:
        realm_name = installations[0]["values"]["IAM_REALM"]
        clients.append(stand_in_client("portal-iam-claims", "Case 7: further claims", realm_name, mappers=[hardcoded("company_id", "c0000099-0000-4000-8000-000000000099"), hardcoded("bpn", "BPNL0000000000XX"), hardcoded("email", "not-for-the-account@example.org")]))
        clients.append(stand_in_client("portal-iam-secret", "Case 6: only a client secret", realm_name, auth="client-secret", secret=env["STAND_IN_SECRET"]))
    users = [{
        "id": stand_in_id(u["key"]), "username": u["key"], "firstName": u["givenName"], "lastName": u["familyName"], "email": f"{u['key']}@stand-in.example.org", "emailVerified": True, "enabled": True,
        "credentials": [{"type": "password", "value": env["TEST_EBW_PASSWORD"], "temporary": False}],
    } for u in stand_ins.values()]
    return {
        "realm": "TEST-EBW", "enabled": True, "sslRequired": "external", "registrationAllowed": False, "accessTokenLifespan": 300,
        "eventsEnabled": True, "eventsListeners": ["jboss-logging"], "enabledEventTypes": ["LOGIN", "LOGIN_ERROR", "CODE_TO_TOKEN", "CODE_TO_TOKEN_ERROR"],
        "requiredActions": [{"alias": "VERIFY_PROFILE", "name": "Verify Profile", "providerId": "VERIFY_PROFILE", "enabled": False, "defaultAction": False, "priority": 90, "config": {}}],
        "clients": clients, "users": users,
    }


def connector_client(values: dict[str, str]) -> dict[str, object]:
    """The Portal IAM of one installation as a client of the EBW-Connector (C5-M1 6.8, entry of its CLIENTS_FILE).
    `page` gives the page of the EBW-Connector the look of the portal UI, so a person sees where they sign in."""
    realm = f"{IAM_URL}/realms/{values['IAM_REALM']}"
    return {
        "clientId": values["EBW_CONNECTOR_CLIENT_ID"], "name": f"Portal IAM of {values['IAM_REALM']}",
        "jwksUri": f"{realm}/protocol/openid-connect/certs", "redirectUris": [f"{realm}/broker/ebw-connector/endpoint"],
        "scopes": ["openid", "profile"],
        "page": {"theme": "tractusx", "brand": "Eclipse Tractus-X", "tagline": "Dataspace Management"},
    }


def sign_in_methods(realm: dict, sign_in: str) -> None:
    """Sets the sign-in methods of a realm (variants wallet, both, password). realm-osp.json describes `wallet`: its
    browser flow redirects to the EBW-Connector at once. The other two use the browser flow of Keycloak, which shows
    the sign-in page: a form for name and password and, if enabled, the button of the identity provider. The
    password is typed only on that page: the direct grant stays denied in every variant."""
    if sign_in in ("both", "password"):
        realm["browserFlow"] = "browser"
    if sign_in == "password":
        realm["identityProviders"][0]["enabled"] = False


def build(variant, source, jwks_base, csp_jwks_url, out, connector_url=None, sign_in=None):
    env = read_env()
    stand_ins = stand_in_users()
    objects = json.loads((TEST / source).read_text(encoding="utf-8"))
    target = out / variant
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.json"):
        old.unlink()
    for item in objects["installations"]:
        values = {
            **COMMON, **item["values"],
            "CSP_JWKS_URL": csp_jwks_url if objects.get("cspJwksFromStandIn") else f"{jwks_base}/csp.json",
            "CALLBACK_JWKS_URL_SA_CREDENTIAL_ISSUER": f"{jwks_base}/credential-issuer.json",
            "C2_M2_CLIENT_SECRET": env["SERVICE_CLIENT_SECRET"], "C2_M3_CLIENT_SECRET": env["SERVICE_CLIENT_SECRET"],
            "CALLBACK_CLIENT_SECRET_SA_IH_CALLBACK": env["SA_IH_CALLBACK_SECRET"], "CALLBACK_CLIENT_SECRET_SA_DIV_CALLBACK": env["SA_DIV_CALLBACK_SECRET"],
        }
        if connector_url:
            values["EBW_CONNECTOR_URL"] = connector_url.rstrip("/")
        realm = json.loads(fill((IAM / "realm-osp.json").read_text(encoding="utf-8"), values))
        if sign_in:
            sign_in_methods(realm, sign_in)
        else:
            # The stand-in is a Keycloak realm, so its paths differ from those of the EBW-Connector (C2-M5 14.1).
            realm["identityProviders"][0]["config"].update({
                "authorizationUrl": f"{STAND_IN}/protocol/openid-connect/auth",
                "tokenUrl": f"{STAND_IN}/protocol/openid-connect/token",
                "jwksUrl": f"{STAND_IN}/protocol/openid-connect/certs",
            })
        service_accounts(realm, env["SERVICE_CLIENT_SECRET"])
        if item.get("technicalUser"):
            technical_user(realm, env["SA_TEST_U1_SECRET"])
        if item.get("appTest"):
            app_test(realm)
        for client in realm["clients"]:
            if client["clientId"] == "portal-ui":
                client["redirectUris"] += ["http://localhost:8081/*", "http://localhost/callback"]
        persons = item.get("persons") or json.loads((ROOT / item["personsFile"]).read_text(encoding="utf-8"))["persons"]
        password = env["TEST_EBW_PASSWORD"] if sign_in in ("both", "password") else None
        realm["users"] += [account(p, stand_ins, password) for p in persons]
        (target / f"{item['values']['IAM_REALM']}-realm.json").write_text(json.dumps(realm, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if connector_url:
        # The file lies beside the variant folder, because Keycloak imports every file in it.
        clients = [connector_client(item["values"]) for item in objects["installations"]]
        text = json.dumps(clients, indent=1, ensure_ascii=False) + "\n"
        (out / f"{variant}.ebw-clients.json").write_text(text, encoding="utf-8")
    if not sign_in:
        stand_in = stand_in_realm(objects["installations"], stand_ins, env, objects.get("standInExtras"))
        text = json.dumps(stand_in, indent=1, ensure_ascii=False) + "\n"
        (target / "TEST-EBW-realm.json").write_text(text, encoding="utf-8")
    print(variant, sorted(p.name for p in target.glob("*.json")))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jwks-base", default="http://iam-test-jwks:8000", help="address of the file server with the test JWKS")
    parser.add_argument("--csp-jwks-url", default="http://host.docker.internal:8100/.well-known/jwks.json", help="JWKS of the CSP stand-in, as Keycloak reaches it (variant hackathon)")
    parser.add_argument("--out", default=str(TEST / "import"), help="target directory")
    parser.add_argument("--sign-in", choices=["wallet", "both", "password"],
                        help="build one more variant with these sign-in methods, without the stand-in TEST-EBW")
    parser.add_argument("--ebw-connector-url",
                        help="address of the EBW-Connector as Keycloak and the browser reach it, for example "
                             "http://localhost:8077; required for --sign-in wallet and both")
    args = parser.parse_args()
    sign_in = args.sign_in or ("wallet" if args.ebw_connector_url else None)
    if sign_in in ("wallet", "both") and not args.ebw_connector_url:
        parser.error(f"--sign-in {sign_in} needs --ebw-connector-url")
    if sign_in == "password" and args.ebw_connector_url:
        parser.error("--sign-in password uses no EBW-Connector: leave out --ebw-connector-url")
    out = Path(args.out)
    build("test", "test-objects.json", args.jwks_base, args.csp_jwks_url, out)
    build("hackathon", "test-objects.hackathon.json", args.jwks_base, args.csp_jwks_url, out)
    if sign_in:
        source = "test-objects.hackathon.json"
        build(sign_in, source, args.jwks_base, args.csp_jwks_url, out, args.ebw_connector_url, sign_in)


if __name__ == "__main__":
    main()

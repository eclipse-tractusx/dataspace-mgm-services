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
"""The steps of App Access in the flows of Process Orchestration (README 8.1 to 8.10), `execute_steps_c2_m2`.
Steps over HTTP give the same answer as the in-process interface (call convention)."""
from __future__ import annotations

from fastapi import Body

from features.app_access import interface
from portal_common.routing import Controller, Permission

controller = Controller("App Access: Process Steps")


@controller.post("/create-client-template", operation_id="stepCreateClientTemplate",
                 summary="Step: create the client template of an approved app")
def step_create_client_template(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.create_client_template(body)


@controller.post("/create-instance-client", operation_id="stepCreateInstanceClient",
                 summary="Step: create an instance client from the template, disabled")
def step_create_instance_client(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.create_instance_client(body)


@controller.post("/enable-instance-client", operation_id="stepEnableInstanceClient",
                 summary="Step: enable an instance client")
def step_enable_instance_client(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.enable_instance_client(body)


@controller.post("/disable-instance-client", operation_id="stepDisableInstanceClient",
                 summary="Step: disable an instance client")
def step_disable_instance_client(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.disable_instance_client(body)


@controller.post("/update-instance-url", operation_id="stepUpdateInstanceUrl",
                 summary="Step: change the URL of an instance")
def step_update_instance_url(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.update_instance_url(body)


@controller.post("/add-app-roles", operation_id="stepAddAppRoles",
                 summary="Step: add app roles to the template and to all instance clients")
def step_add_app_roles(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.add_app_roles(body)


@controller.post("/update-role-descriptions", operation_id="stepUpdateRoleDescriptions",
                 summary="Step: replace the descriptions of app roles")
def step_update_role_descriptions(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.update_role_descriptions(body)


@controller.post("/assign-company-admin", operation_id="stepAssignCompanyAdmin",
                 summary="Step: bind the account of the applicant and make it Company Admin")
def step_assign_company_admin(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.assign_company_admin(body)


@controller.post("/disable-company-users", operation_id="stepDisableCompanyUsers",
                 summary="Step: remove company and roles from the accounts of a deactivated company")
def step_disable_company_users(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.disable_company_users(body)


@controller.post("/enable-company-users", operation_id="stepEnableCompanyUsers",
                 summary="Step: give company and roles back to the accounts of a reactivated company")
def step_enable_company_users(body: dict = Body(...), _: dict = Permission) -> interface.Json:
    return interface.enable_company_users(body)

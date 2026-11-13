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
#  Assisted-By: GitHub Copilot (claude-opus-5.5)
"""The applicant's own applications (README 7.2 to 7.6, 7.10, 7.11).

The scope `own` is applied by the services, which answer 404 for other people (README 6.3).
"""
from __future__ import annotations

from fastapi import Body, Query, Request, Response

from features.registration.models.value_sets import Status
from features.registration.services import application_service, application_views
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("Registration: Applications")


@controller.post("", status_code=201)
def create_application(request: Request, response: Response, body: dict = Body(...), claims: dict = Permission):
    application, created = application_service.create_application(body, claims)
    if created:
        response.headers["Location"] = f"{request.url.path}/{application['id']}"
    else:
        response.status_code = 200
    return application


@controller.get("")
def list_applications(status: list[Status] | None = Query(None), page: int = Page, size: int = Size,
                      claims: dict = Permission):
    return application_service.list_own(claims["sub"], status, page, size)


@controller.get("/{applicationId}")
def get_application(applicationId: str, claims: dict = Permission):
    return application_views.with_review(application_service.own(claims["sub"], applicationId))


@controller.patch("/{applicationId}")
def update_application(applicationId: str, body: dict = Body(...), claims: dict = Permission):
    return application_service.update_application(applicationId, claims["sub"], body)


@controller.put("/{applicationId}/attestation")
def replace_attestation(applicationId: str, body: dict = Body(...), claims: dict = Permission):
    return application_service.replace_attestation(applicationId, claims, body.get("attestation"))


@controller.post("/{applicationId}/submit")
def submit_application(applicationId: str, body: dict = Body(...), claims: dict = Permission):
    return application_service.submit_application(applicationId, claims["sub"], body)


@controller.post("/{applicationId}/withdraw")
def withdraw_application(applicationId: str, claims: dict = Permission):
    return application_service.withdraw_application(applicationId, claims["sub"])

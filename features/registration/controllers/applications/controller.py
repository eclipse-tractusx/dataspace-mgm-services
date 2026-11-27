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

from features.registration import interface
from features.registration.models.applications import Application, ApplicationSummary, ApplicationWithReview
from features.registration.models.value_sets import ApplicationStatus
from portal_common.models import Page as PageOf
from portal_common.routing import Controller, Page, Permission, Size

controller = Controller("Registration: Applications")
"""The bodies stay `dict` here: the services check them in the order of README 7.2 to 7.10 (403, 404 and 409
before field errors, with the messages of README 6) and then read them into `ApplicationCreate`,
`ApplicationUpdate` and `SubmitRequest`."""


@controller.post("", status_code=201, response_model=Application, response_model_exclude_unset=True)
def create_application(request: Request, response: Response, body: dict = Body(...),
                       claims: dict = Permission) -> Application:
    application, created = interface.create_application(body, claims)
    if created:
        response.headers["Location"] = f"{request.url.path}/{application.id}"
    else:
        response.status_code = 200
    return application


@controller.get("", response_model=PageOf[ApplicationSummary], response_model_exclude_unset=True)
def list_applications(status: list[ApplicationStatus] | None = Query(None), page: int = Page, size: int = Size,
                      claims: dict = Permission) -> PageOf[ApplicationSummary]:
    return interface.list_own(claims["sub"], status, page, size)


@controller.get("/{applicationId}", response_model=ApplicationWithReview, response_model_exclude_unset=True)
def get_application(applicationId: str, claims: dict = Permission) -> ApplicationWithReview:
    return interface.get_own_application(claims["sub"], applicationId)


@controller.patch("/{applicationId}", response_model=Application, response_model_exclude_unset=True)
def update_application(applicationId: str, body: dict = Body(...), claims: dict = Permission) -> Application:
    return interface.update_application(applicationId, claims["sub"], body)


@controller.put("/{applicationId}/attestation", response_model=Application, response_model_exclude_unset=True)
def replace_attestation(applicationId: str, body: dict = Body(...), claims: dict = Permission) -> Application:
    return interface.replace_attestation(applicationId, claims, body.get("attestation"))


@controller.post("/{applicationId}/submit", response_model=Application, response_model_exclude_unset=True)
def submit_application(applicationId: str, body: dict = Body(...), claims: dict = Permission) -> Application:
    return interface.submit_application(applicationId, claims["sub"], body)


@controller.post("/{applicationId}/withdraw", response_model=Application, response_model_exclude_unset=True)
def withdraw_application(applicationId: str, claims: dict = Permission) -> Application:
    return interface.withdraw_application(applicationId, claims["sub"])

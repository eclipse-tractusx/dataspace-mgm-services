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
"""The steps on the people of a company (README 8.8 to 8.10): the company admin from onboarding, and all people of a
company disabled and enabled again with the company. Bindings and roles go through `UserServiceImpl`."""
from __future__ import annotations

from features.app_access.managers.dao import DaoService
from features.app_access.models import AssignCompanyAdminResult, CompanyUsersResult
from features.app_access.models.common import Actor
from features.app_access.models.constants import (
    BindingStatus,
    CompanyStatus,
    InvitationEndReason,
    InvitationStatus,
    JoinedVia,
    RoleKind,
)
from features.app_access.models.exception import (
    ConflictException,
    InvalidStateException,
    StaffCompanyConflictException,
    UserAlreadyBoundException,
    UserNotFoundException,
)
from features.app_access.models.internal import Company, CompanyUser
from features.app_access.services.context import Context
from features.app_access.services.ports import CompanyUsersSteps
from portal_common import settings

from .user_service_impl import UserServiceImpl


class CompanyUsersStepsImpl(CompanyUsersSteps):
    def __init__(self, ctx: Context, users: UserServiceImpl) -> None:
        self.ctx = ctx
        self.users = users

    @property
    def dao(self) -> DaoService:
        return self.ctx.dao

    # -- 8.8 ----------------------------------------------------------------------------------------
    def assign_company_admin(self, input: dict) -> AssignCompanyAdminResult:
        """8.8"""
        v = self.ctx.validate
        company_id, bpn, user_id = v.uuid(input, "companyId"), v.bpn(input), v.text(input, "applicantSub")
        actor = Actor.process(input)
        with self.dao.lock(("company", company_id), ("account", user_id)):
            company = self.dao.companies.get(company_id)
            self._check_company(company, bpn)
            user = self.ctx.iam.get_user(user_id)
            if user is None:
                raise UserNotFoundException("account unknown in the Portal IAM", retryable=False)
            binding = self.dao.company_users.current_of(user_id)
            self._check_binding(binding, company_id, user_id)
            company = self._company_for_admin(company, company_id, bpn)
            if binding is None:
                self.users.bind(user_id, company, [self._admin_role()], JoinedVia.ONBOARDING, actor,
                                "assign-company-admin", given_name=user.get("firstName"),
                                family_name=user.get("lastName"))
            else:
                self._admin_of_bound(binding, company, user, actor)
            return AssignCompanyAdminResult(company_id=company_id, user_id=user_id,
                                            portal_roles=self.users.company_roles(user_id))

    def _admin_role(self) -> str:
        return self.ctx.config.from_properties("company.admin.role")

    @staticmethod
    def _check_company(company: Company | None, bpn: str) -> None:
        if company is not None and company.bpn != bpn:
            raise ConflictException("the BPN differs from the stored one", retryable=False)
        if company is not None and company.status in (CompanyStatus.DISABLING, CompanyStatus.ENABLING):
            raise InvalidStateException(f"company status {company.status}", retryable=True)

    def _check_binding(self, binding: CompanyUser | None, company_id: str, user_id: str) -> None:
        if binding is not None and binding.company_id != company_id:
            raise UserAlreadyBoundException("the account is bound to another company", retryable=False)
        if binding is None and company_id != settings.get("ospCompanyId") and self.users.has_staff_role(user_id):
            raise StaffCompanyConflictException("staff accounts bind only to the OSP company", retryable=False)

    def _company_for_admin(self, company: Company | None, company_id: str, bpn: str) -> Company:
        """The company of the step: created on first onboarding, active again after a transfer (FRAMEWORK 5.6)."""
        if company is None:
            company = Company(company_id, bpn)
            self.dao.companies.save(company)
        elif company.status == CompanyStatus.DISABLED:
            self.users.set_company_status(company, CompanyStatus.ACTIVE)
        return company

    def _admin_of_bound(self, binding: CompanyUser, company: Company, user: dict, actor: Actor) -> None:
        """An account already bound to the company: restored if disabled, and the admin role added if missing."""
        operation, user_id, company_id = "assign-company-admin", binding.user_id, company.company_id
        admin = self._admin_role()
        restored = binding.status == BindingStatus.DISABLED
        if restored:
            self.users.restore(binding, company, actor, operation)
        else:
            self.users.set_company_attributes(self.ctx.iam.get_user(user_id) or user, company)
        added = [] if admin in self.users.portal_roles(user_id) else [admin]
        if added:
            self.ctx.iam.add_client_role_mappings(user_id, self.ctx.core_uuid, [self.ctx.core_role(admin)])
            self.users.log_roles(actor, operation, user_id, company_id, RoleKind.COMPANY_PORTAL, added, [])
            self.ctx.audit(actor, operation, company_id, user_id)
        if restored:
            self.ctx.publish("UserAssignedToCompany", {"userId": user_id, "companyId": company_id,
                                                       "via": str(JoinedVia.ONBOARDING),
                                                       "portalRoles": self.users.company_roles(user_id)})
        elif added:
            self.ctx.publish("UserRolesChanged", {"userId": user_id, "companyId": company_id,
                                                  "addedRoles": added, "removedRoles": []})

    # -- 8.9 and 8.10 -------------------------------------------------------------------------------
    def _user_ids(self, company_id: str, status: BindingStatus) -> list[str]:
        return sorted(b.user_id for b in self.dao.company_users.list_of_company(company_id, [status]))

    def disable_company_users(self, input: dict) -> CompanyUsersResult:
        """8.9"""
        company_id = self.ctx.validate.uuid(input, "companyId")
        actor, dao, operation = Actor.process(input), self.dao, "disable-company-users"
        if company_id == settings.get("ospCompanyId"):
            raise InvalidStateException("the OSP company is not deactivated by this step", retryable=False)
        with dao.lock(("company", company_id)):
            company = dao.companies.get(company_id)
            if company is None:
                return CompanyUsersResult(company_id=company_id, user_ids=[])
            if company.status == CompanyStatus.ENABLING:
                raise InvalidStateException("the company is being enabled", retryable=True)
            if company.status == CompanyStatus.ACTIVE:
                self.users.set_company_status(company, CompanyStatus.DISABLING)
                self._revoke_open_invitations(company_id)
                self.ctx.audit(actor, operation, company_id, company_id)
            if company.status == CompanyStatus.DISABLING:
                for binding in dao.company_users.list_of_company(company_id, [BindingStatus.ACTIVE]):
                    with dao.lock(("account", binding.user_id)):
                        self.users.suspend(binding, actor, operation)
                self.users.set_company_status(company, CompanyStatus.DISABLED)
                self.ctx.publish("CompanyUsersDisabled", {
                    "companyId": company_id, "userIds": self._user_ids(company_id, BindingStatus.DISABLED)})
            return CompanyUsersResult(company_id=company_id,
                                      user_ids=self._user_ids(company_id, BindingStatus.DISABLED))

    def _revoke_open_invitations(self, company_id: str) -> None:
        for inv in self.dao.invitations.list_all():
            if inv.company_id == company_id and inv.status == InvitationStatus.OPEN:
                inv.end(InvitationStatus.REVOKED, InvitationEndReason.COMPANY_DISABLED)
                self.dao.invitations.save(inv)

    def enable_company_users(self, input: dict) -> CompanyUsersResult:
        """8.10"""
        company_id = self.ctx.validate.uuid(input, "companyId")
        actor, dao, operation = Actor.process(input), self.dao, "enable-company-users"
        with dao.lock(("company", company_id)):
            company = dao.companies.get(company_id)
            if company is None:
                return CompanyUsersResult(company_id=company_id, user_ids=[])
            if company.status == CompanyStatus.DISABLING:
                raise InvalidStateException("the company is being disabled", retryable=True)
            announce = company.status != CompanyStatus.ACTIVE
            if company.status == CompanyStatus.DISABLED:
                self.users.set_company_status(company, CompanyStatus.ENABLING)
            for binding in dao.company_users.list_of_company(company_id, [BindingStatus.DISABLED]):
                with dao.lock(("account", binding.user_id)):
                    self.users.restore(binding, company, actor, operation)
            user_ids = self._user_ids(company_id, BindingStatus.ACTIVE)
            if announce:
                self.users.set_company_status(company, CompanyStatus.ACTIVE)
                self.ctx.publish("CompanyUsersEnabled", {"companyId": company_id, "userIds": user_ids})
            return CompanyUsersResult(company_id=company_id, user_ids=user_ids)

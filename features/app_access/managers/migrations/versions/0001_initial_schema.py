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
"""Initial schema of the database c2_m2 (README section 5), generated from the SQLModel tables of
`models/tables.py` (`alembic revision --autogenerate` against an empty database).

Revision ID: 0001
Revises:
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _index(table: str, column: str) -> None:
    op.create_index(op.f(f"ix_{table}_{column}"), table, [column], unique=False)


def _create_app_client_template() -> None:
    op.create_table('app_client_template',
    sa.Column('app_id', sa.String(), nullable=False),
    sa.Column('provider_company_id', sa.String(), nullable=False),
    sa.Column('app_name', sa.String(), nullable=False),
    sa.Column('iam_client_id', sa.String(), nullable=False),
    sa.Column('iam_client_uuid', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('app_id'),
    sa.UniqueConstraint('iam_client_id')
    )


def _create_app_instance_client() -> None:
    op.create_table('app_instance_client',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('app_id', sa.String(), nullable=False),
    sa.Column('instance_kind', sa.String(), nullable=False),
    sa.Column('offer_subscription_id', sa.String(), nullable=True),
    sa.Column('customer_company_id', sa.String(), nullable=True),
    sa.Column('iam_client_id', sa.String(), nullable=False),
    sa.Column('instance_url', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('iam_client_uuid', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('iam_client_id'),
    sa.UniqueConstraint('offer_subscription_id')
    )
    _index('app_instance_client', 'app_id')
    _index('app_instance_client', 'created_at')
    _index('app_instance_client', 'customer_company_id')


def _create_audit_log() -> None:
    op.create_table('audit_log',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('actor', sa.JSON(), nullable=False),
    sa.Column('operation', sa.String(), nullable=False),
    sa.Column('company_id', sa.String(), nullable=True),
    sa.Column('object_id', sa.String(), nullable=True),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    _index('audit_log', 'occurred_at')


def _create_client_number() -> None:
    op.create_table('client_number',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )


def _create_company() -> None:
    op.create_table('company',
    sa.Column('company_id', sa.String(), nullable=False),
    sa.Column('bpn', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('company_id')
    )


def _create_company_user() -> None:
    op.create_table('company_user',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('company_id', sa.String(), nullable=False),
    sa.Column('joined_via', sa.String(), nullable=False),
    sa.Column('given_name', sa.String(), nullable=True),
    sa.Column('family_name', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('invitation_id', sa.String(), nullable=True),
    sa.Column('removal_reason', sa.String(), nullable=True),
    sa.Column('suspended_roles', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    _index('company_user', 'company_id')
    _index('company_user', 'status')
    _index('company_user', 'user_id')


def _create_invitation() -> None:
    op.create_table('invitation',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('company_id', sa.String(), nullable=True),
    sa.Column('given_name', sa.String(), nullable=True),
    sa.Column('family_name', sa.String(), nullable=True),
    sa.Column('roles', sa.JSON(), nullable=False),
    sa.Column('code_hash', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('end_reason', sa.String(), nullable=True),
    sa.Column('failed_attempts', sa.Integer(), nullable=False),
    sa.Column('accepted_by', sa.String(), nullable=True),
    sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code_hash')
    )
    _index('invitation', 'company_id')
    _index('invitation', 'created_at')
    _index('invitation', 'kind')


def _create_role_assignment_log() -> None:
    op.create_table('role_assignment_log',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('company_id', sa.String(), nullable=True),
    sa.Column('role_kind', sa.String(), nullable=False),
    sa.Column('iam_client_id', sa.String(), nullable=False),
    sa.Column('role_name', sa.String(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('actor', sa.JSON(), nullable=False),
    sa.Column('operation', sa.String(), nullable=False),
    sa.Column('app_id', sa.String(), nullable=True),
    sa.Column('app_instance_client_id', sa.String(), nullable=True),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    _index('role_assignment_log', 'occurred_at')
    _index('role_assignment_log', 'user_id')


def upgrade() -> None:
    _create_app_client_template()
    _create_app_instance_client()
    _create_audit_log()
    _create_client_number()
    _create_company()
    _create_company_user()
    _create_invitation()
    _create_role_assignment_log()


def downgrade() -> None:
    op.drop_index(op.f('ix_role_assignment_log_user_id'), table_name='role_assignment_log')
    op.drop_index(op.f('ix_role_assignment_log_occurred_at'), table_name='role_assignment_log')
    op.drop_table('role_assignment_log')
    op.drop_index(op.f('ix_invitation_kind'), table_name='invitation')
    op.drop_index(op.f('ix_invitation_created_at'), table_name='invitation')
    op.drop_index(op.f('ix_invitation_company_id'), table_name='invitation')
    op.drop_table('invitation')
    op.drop_index(op.f('ix_company_user_user_id'), table_name='company_user')
    op.drop_index(op.f('ix_company_user_status'), table_name='company_user')
    op.drop_index(op.f('ix_company_user_company_id'), table_name='company_user')
    op.drop_table('company_user')
    op.drop_table('company')
    op.drop_table('client_number')
    op.drop_index(op.f('ix_audit_log_occurred_at'), table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index(op.f('ix_app_instance_client_customer_company_id'), table_name='app_instance_client')
    op.drop_index(op.f('ix_app_instance_client_created_at'), table_name='app_instance_client')
    op.drop_index(op.f('ix_app_instance_client_app_id'), table_name='app_instance_client')
    op.drop_table('app_instance_client')
    op.drop_table('app_client_template')

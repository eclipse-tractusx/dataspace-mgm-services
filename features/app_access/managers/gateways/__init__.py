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
"""Neighbours of App Access (C3-M1 company profiles, C10-M1 subscriptions) through `portal_common.neighbours`, with
the built-in stand-ins of README 11.2 read from `managers/data/`, and the keys of the EBW-Connector (C5-M1)."""
from .attestation_keys_impl import AttestationKeysImpl
from .company_profile_gateway_impl import CompanyProfileGatewayImpl
from .neighbour_gateway import NeighbourGateway
from .subscriptions_gateway_impl import SubscriptionsGatewayImpl

__all__ = ["AttestationKeysImpl", "CompanyProfileGatewayImpl", "NeighbourGateway", "SubscriptionsGatewayImpl"]

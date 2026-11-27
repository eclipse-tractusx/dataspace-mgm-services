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
"""Portal IAM adapters of App Access: the Keycloak Admin API, or the in-memory test IAM without `IAM_URL`."""
from features.app_access.managers.config import Config
from features.app_access.managers.ports import PortalIam

from .keycloak_portal_iam import KeycloakPortalIam


def portal_iam(config: Config) -> PortalIam:
    """The Keycloak Admin API at `IAM_URL`, or in-memory test IAM when `iam.url` is empty."""
    if not config.from_properties("iam.url"):
        from .test_iam_portal_iam import TestIamPortalIamAdapter
        return TestIamPortalIamAdapter(config)
    return KeycloakPortalIam(config)


__all__ = ["KeycloakPortalIam", "portal_iam"]

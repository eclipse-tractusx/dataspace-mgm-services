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
#  Assisted-By: GitHub Copilot (GPT-5.1)
#################################################################################
"""In-process contract for the optional IssuerService caller.

The caller never sends a DCP offer from the issuer side. Issuance is started by
one request to the holder wallet; the wallet then performs DCP with the issuer.
"""

from features.dataspace_issuer_interface.exceptions.issuer_caller_error import IssuerCallerError
from features.dataspace_issuer_interface.models.holder_registration import HolderRegistration
from features.dataspace_issuer_interface.services.issuer_caller import IssuerCaller


class DataspaceIssuerInterface:
    """Public in-process interface for the optional IssuerService caller."""

    def __init__(self, caller: IssuerCaller | None = None):
        self._caller = caller or IssuerCaller()

    def register_holder(self, request: HolderRegistration) -> None:
        """Register a company's wallet DID in the issuer participant context."""
        self._caller.register_holder(request)

    def get_holders(self) -> list[dict[str, object]]:
        """Return holders registered in the configured IssuerService participant context."""
        return self._caller.get_holders()

    def get_holder(self, holder_id: str) -> dict[str, object]:
        """Return a holder by ID from the configured IssuerService participant context."""
        return self._caller.get_holder(holder_id)

_interface = DataspaceIssuerInterface()
get_holder = _interface.get_holder
register_holder = _interface.register_holder
get_holders = _interface.get_holders

__all__ = [
    "DataspaceIssuerInterface",
    "HolderRegistration",
    "IssuerCallerError",
    "get_holder",
    "get_holders",
    "register_holder",
]

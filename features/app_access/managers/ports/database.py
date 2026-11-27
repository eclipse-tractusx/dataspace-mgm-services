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
"""The unit of work of the module's own database `c2_m2` (README 4, 6.14), as the DAOs and `DaoService` need it."""
from __future__ import annotations

import abc
from contextlib import AbstractContextManager


class Database(abc.ABC):
    @abc.abstractmethod
    def transaction(self) -> AbstractContextManager[None]:
        """One transaction for everything inside; nested calls join the open one."""

    @abc.abstractmethod
    def lock(self, name: str) -> AbstractContextManager[None]:
        """Holds the named lock (README 6.14) until the open transaction ends; opens one when none is open."""

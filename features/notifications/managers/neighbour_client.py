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
"""Calls of the neighbours C2-M2 and C10-M1 (README 4, FRAMEWORK 4.7) through `portal_common.neighbours`.

A neighbour that cannot be reached (`retryable` problem) raises `store.Unavailable`, so the worker repeats
the job (README 4); a neighbour that rejects the call raises its `Problem` at once, since repeating cannot help.
"""
from __future__ import annotations

from features.notifications.managers import store
from features.notifications.models import MODULE
from portal_common import neighbours
from portal_common.problems import Problem


def is_standin(target: str) -> bool:
    """True if the address of `target` is empty: the built-in stand-in of README 11.2 answers."""
    return neighbours.is_standin(target)


def query(target: str, function: str, **params: object) -> list | dict | None:
    """`neighbours.query` with the retry rule of README 4: unreachable -> `store.Unavailable`. The answer is the
    JSON of the neighbour's query (a list or an object), or None."""
    try:
        return neighbours.query(MODULE, target, function, **params)
    except Problem as e:
        if e.ext.get("retryable"):
            raise store.Unavailable(f"{target} {function}: {e.name}") from e
        raise

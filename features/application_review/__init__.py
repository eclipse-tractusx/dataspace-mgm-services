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
"""Application Review (spec C1-M3): OSP staff review a submitted application.

The step `open-review` opens a review case and runs the automatic pre-check; reviewers approve (with four eyes
where configured) or decline; the step `close-review` closes the case of a withdrawn application.

Index of the feature (layout in `features/__init__.py`): `NAME`, `MODULE` and the lifecycle hooks a runtime
calls, `reset()` and `on_startup()`. The HTTP API is `features.application_review.router.router`.
"""
from __future__ import annotations

from features.application_review import services
from features.application_review.models.value_sets import MODULE

NAME = "application_review"

__all__ = ["MODULE", "NAME", "on_startup", "reset"]


def reset() -> None:
    services.reset()


def on_startup() -> None:
    services.start()   # checks the configuration (README 4, 6.6) and creates the tables

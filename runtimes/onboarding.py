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
"""Hybrid runtime of the onboarding: registration and company profile in one pod.

The two features call each other in-process; Process Orchestration and the other modules are
neighbours in their own runtimes (`MODULE_URLS`). Splitting them later is a deployment change only:
run `features/registration/main.py` and `features/company_profile/main.py` instead.
"""
from __future__ import annotations

from fastapi import FastAPI

from features import company_profile, registration
from runtimes import create_runtime, serve

FEATURES = (registration, company_profile)


def create_app() -> FastAPI:
    return create_runtime(*FEATURES)


if __name__ == "__main__":
    serve(create_app)

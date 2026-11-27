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
#  SPDX-License-Identifier: Apache-2.0
#################################################################################
"""Operations & Orchestration domain runtime (ADR-0003, ADR-0005).

Serves Notifications (C11-M1) and Process Orchestration (C12-M1) in an
asynchronous events and process execution cluster.
"""
from __future__ import annotations

import importlib.util
from typing import Any

from fastapi import FastAPI

from features import notifications
from runtimes import create_runtime, serve

FEATURES: list[Any] = [notifications]

if importlib.util.find_spec("features.process_orchestration"):
    FEATURES.append(importlib.import_module("features.process_orchestration"))
else:
    FEATURES.append("c12-m1")


def create_app() -> FastAPI:
    return create_runtime(*FEATURES)


if __name__ == "__main__":
    serve(create_app)

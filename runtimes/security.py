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
"""Access & Security domain runtime (ADR-0003, ADR-0005).

Serves Technical Users (C2-M3), Credentials (C4-M1), App Access (C2-M2),
and Dataspace Wallet Interface (C4-M2) in a secure identity cluster.
"""
from __future__ import annotations

import importlib.util
from typing import Any

from fastapi import FastAPI

from features import credentials, technical_user
from runtimes import create_runtime, serve

FEATURES: list[Any] = [technical_user, credentials]

# Dynamically bind migrated features or fallback to module spec IDs
for feat_name, spec_id in (("app_access", "c2-m2"), ("dataspace_wallet_interface", "c4-m2")):
    if importlib.util.find_spec(f"features.{feat_name}"):
        FEATURES.append(importlib.import_module(f"features.{feat_name}"))
    else:
        FEATURES.append(spec_id)


def create_app() -> FastAPI:
    return create_runtime(*FEATURES)


if __name__ == "__main__":
    serve(create_app)

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
"""The signing key of OSP A and the trust list of the CSP stand-in, as `demo.py` writes them (test keys).

Runs once per start in the volume `keys`: an existing key is kept, so the installation keeps its key over
restarts. The files belong to the user of the backend image, which reads them and lets the CSP stand-in
create its own key there.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app")
from tools.keys import load_or_create_ec  # noqa: E402

KEYS = Path("/keys")
UID = GID = 10001   # user of the backend image (Dockerfile)

settings = json.loads(Path("/app/config/osp-a/installation.json").read_text())
_, public = load_or_create_ec(KEYS / "osp-a-key.json", "osp-a-1")
iam = os.environ["IAM_PUBLIC_URL"].rstrip("/")
trust = {settings["ospId"]: {"name": settings["ospName"], "installationUrl": os.environ["BACKEND_URL"], "jwk": public,
                             "iamTokenUrl": f"{iam}/realms/{os.environ['IAM_REALM']}/protocol/openid-connect/token"}}
(KEYS / "csp-trust.json").write_text(json.dumps(trust, indent=2))
for path in (KEYS, *KEYS.iterdir()):
    os.chown(path, UID, GID)
print("keys ready:", ", ".join(sorted(p.name for p in KEYS.iterdir())))

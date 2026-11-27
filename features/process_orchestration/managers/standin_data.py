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
"""Answers of the built-in stand-in (README 11.3): a neighbour with an empty address answers its steps `DONE`
at once with these results, and its lookups with the data of README 14 (`data/standin.json`).
`STANDIN_FILE` replaces single entries of both."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from features.process_orchestration.managers import config

DEFAULTS = Path(__file__).parent / "data" / "standin.json"


def load() -> dict:
    """`{"steps": {<module>.<step>: result}, "lookups": {<module>.<operationId>: answer}}`, a fresh copy."""
    answers = json.loads(DEFAULTS.read_text(encoding="utf-8"))
    extra_file = config.standin_file()
    if extra_file:
        extra = yaml.safe_load(Path(extra_file).read_text(encoding="utf-8")) or {}
        for part in ("steps", "lookups"):
            answers[part].update(extra.get(part) or {})
    return answers

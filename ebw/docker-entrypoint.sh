#!/bin/sh
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
#  Assisted-By: Claude Code (claude-fable-5-2)
#################################################################################

# Starts one service of the EBW stack in a container. `EBW_SERVICE` names it: connector, business_wallet or
# test_tools. Keys and data go to `/data/<service>/` unless KEY_DIR and DATA_DIR say otherwise, so the three
# services can share one volume. Called with `healthcheck`, it asks the service of this container for its page.
set -eu

SERVICE="${EBW_SERVICE:-connector}"
case "${SERVICE}" in
  connector) PORT="${PORT:-8077}" ;;
  business_wallet) PORT="${PORT:-8078}" ;;
  test_tools) PORT="${PORT:-8079}" ;;
  *)
    echo "EBW_SERVICE must be connector, business_wallet or test_tools, not '${SERVICE}'" >&2
    exit 64
    ;;
esac

if [ "${1:-}" = "healthcheck" ]; then
  exec wget -q -O /dev/null "http://127.0.0.1:${PORT}/"
fi

HOME_DIR="${EBW_DATA_DIR:-/data}"
export KEY_DIR="${KEY_DIR:-${HOME_DIR}/${SERVICE}/keys}"
export DATA_DIR="${DATA_DIR:-${HOME_DIR}/${SERVICE}/data}"
if [ "${SERVICE}" = "connector" ]; then
  export AUDIT_LOG_FILE="${AUDIT_LOG_FILE:-${DATA_DIR}/audit.log}"
  # the test tools write the public key of their trust list here (same volume)
  export TRUST_LIST_SIGNER_FILE="${TRUST_LIST_SIGNER_FILE:-${HOME_DIR}/test_tools/keys/trust-list-signer.json}"
fi
mkdir -p "${KEY_DIR}" "${DATA_DIR}"

exec python -m uvicorn "${SERVICE}.app:app" --host 0.0.0.0 --port "${PORT}"

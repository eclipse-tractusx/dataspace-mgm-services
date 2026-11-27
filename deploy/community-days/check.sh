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
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
# Waits until the stack of this folder is up, then checks it. Exit code 0 = everything OK.
# Usage (in this folder): sh check.sh [seconds to wait, default 600]
cd "$(dirname "$0")" || exit 1
WAIT="${1:-600}"
# the settings of .env, if any, as docker compose reads them
[ -f .env ] && { set -a; . ./.env; set +a; }
PORTAL="http://localhost:${PORTAL_PORT:-3000}"
IAM="http://localhost:${KEYCLOAK_PORT:-8080}/auth"

echo "Waiting up to $WAIT s for all services (docker compose ps) ..."
end=$(( $(date +%s) + WAIT ))
while :; do
  states="$(docker compose ps -a --format '{{.Service}}|{{.State}}|{{.Health}}|{{.ExitCode}}' 2>/dev/null)"
  waiting="$(echo "$states" | awk -F'|' '$1!="keys" && $3!="healthy"')"
  failed="$(echo "$states" | awk -F'|' '($1=="keys" && $2=="exited" && $4!="0") || ($1!="keys" && $2=="exited")')"
  [ -n "$states" ] && [ -z "$waiting" ] && break
  if [ -n "$failed" ]; then echo "FAILED to start:"; echo "$failed"; echo "See: docker compose logs <service>"; exit 1; fi
  if [ "$(date +%s)" -ge "$end" ]; then echo "Not ready after $WAIT s:"; echo "${waiting:-no services, run: docker compose up -d --build}"; exit 1; fi
  sleep 5
done
echo "All services healthy."

FAIL=0
check() {   # label expected-status actual-status
  if [ "$2" = "$3" ]; then echo "OK    $1 ($3)"; else echo "FAIL  $1 (expected $2, got $3)"; FAIL=1; fi
}
code() { curl -s --noproxy '*' -o /dev/null -w '%{http_code}' "$@"; }

check "portal index        $PORTAL/" 200 "$(code "$PORTAL/")"
check "BFF health          $PORTAL/health" 200 "$(code "$PORTAL/health")"
check "backend health      (inside the network)" 200 \
  "$(docker compose exec -T backend wget -q -O /dev/null http://127.0.0.1:8000/health && echo 200 || echo error)"
check "Keycloak discovery  $IAM/realms/CX-Central" 200 "$(code "$IAM/realms/CX-Central/.well-known/openid-configuration")"
check "/me without session $PORTAL/me" 401 "$(code "$PORTAL/me")"

if [ "$FAIL" = 0 ]; then echo "Everything OK. Portal: ${PORTAL_URL:-$PORTAL}"; else echo "Some checks failed."; fi
exit "$FAIL"

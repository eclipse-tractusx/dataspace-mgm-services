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

# Container image of the EBW stack: EBW-Connector, Business Wallet and test tools in one image.
# `EBW_SERVICE` picks the service of a container: `connector` (default, port 8077), `business_wallet` (8078)
# or `test_tools` (8079). The three containers share one volume at `/data`: keys and data of each service,
# and the signer key of the trust list that the EBW-Connector reads from the test tools.
#
# Build (in this folder):  docker build -t ebw-stack:local .
# Run one service:         docker run --rm -p 8077:8077 -v ebw-data:/data -e EBW_SERVICE=connector \
#                              -e PUBLIC_URL=http://localhost:8077 --read-only ebw-stack:local
# Kubernetes:              charts/ebw-stack

# ---- Build stage: install the pinned dependencies into a virtual environment ----
FROM python:3.12-alpine AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, so that the layer is cached as long as requirements.txt does not change
COPY requirements.txt ./
RUN python -m venv /app/.venv \
    && /app/.venv/bin/pip install -r requirements.txt

COPY common ./common
COPY connector ./connector
COPY business_wallet ./business_wallet
COPY test_tools ./test_tools
COPY docker-entrypoint.sh ./

# ---- Runtime stage: official Python image, as-is, plus a non-root user ----
FROM python:3.12-alpine

ARG UID=10001
ARG GID=10001

RUN addgroup -g "${GID}" -S app \
    && adduser -u "${UID}" -G app -S -D -H -h /app app \
    && mkdir -p /data \
    && chown "${UID}:${GID}" /data

WORKDIR /app

# The application files belong to root and are read-only for the application user
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    EBW_SERVICE=connector

USER ${UID}:${GID}

EXPOSE 8077 8078 8079

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/app/docker-entrypoint.sh", "healthcheck"]

CMD ["/app/docker-entrypoint.sh"]

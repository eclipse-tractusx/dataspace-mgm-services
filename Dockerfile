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

# Container image of the Eclipse Tractus-X Dataspace Management Service (backend).
# Build:  docker build -t tractusx/dataspace-mgm-service:local .
# Run:    docker run --rm -p 8000:8000 --read-only --tmpfs /tmp tractusx/dataspace-mgm-service:local
# Notice for the image on DockerHub: DOCKER_NOTICE.md (TRG 4.06)

# ---- Build stage: install the locked dependencies into a virtual environment ----
FROM python:3.15-alpine AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN pip install "uv>=0.9,<1"

# Dependencies first, so that the layer is cached as long as uv.lock does not change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# ---- Runtime stage: official Python image, as-is, plus a non-root user (TRG 4.02, TRG 4.03) ----
FROM python:3.15-alpine

ARG UID=10001
ARG GID=10001

RUN addgroup -g "${GID}" -S app \
    && adduser -u "${UID}" -G app -S -D -H -h /app app

WORKDIR /app

# The application files belong to root and are read-only for the application user (TRG 4.07)
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER ${UID}:${GID}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "--factory", "scaffold.app:create_app", "--host", "0.0.0.0", "--port", "8000"]

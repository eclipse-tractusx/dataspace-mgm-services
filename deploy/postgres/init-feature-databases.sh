#!/usr/bin/env bash
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

set -e

# Idempotent database and role provisioning for Eclipse Tractus-X OSP 2.0 (ADR-0003, ADR-0005)
# Creates a dedicated PostgreSQL user, password, and database for each of the 13 modular features.
# Executed automatically by PostgreSQL container entrypoint (/docker-entrypoint-initdb.d/).

FEATURES=(
  "registration"
  "application_review"
  "app_access"
  "technical_user"
  "company_profile"
  "csp_connection"
  "credentials"
  "dataspace_wallet_interface"
  "connector"
  "offers"
  "subscriptions"
  "notifications"
  "process_orchestration"
)

echo "Starting automated provisioning of feature databases for Eclipse Tractus-X..."

for feature in "${FEATURES[@]}"; do
  echo "Provisioning feature database and role for: $feature"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$feature') THEN
        CREATE ROLE $feature WITH LOGIN PASSWORD '${feature}_test_pass';
      END IF;
    END \$\$;
EOSQL

  # Create database if not exists
  if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -lqt | cut -d \| -f 1 | grep -qw "$feature"; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE DATABASE $feature OWNER $feature;"
  fi

  # Grant privileges on public schema
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$feature" <<-EOSQL
    GRANT ALL ON SCHEMA public TO $feature;
EOSQL
done

echo "Successfully provisioned all 13 feature databases."

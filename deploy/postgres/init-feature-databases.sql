-- ==============================================================================
-- Copyright (c) 2026 Contributors to the Eclipse Foundation
--
-- See the NOTICE file(s) distributed with this work for additional
-- information regarding copyright ownership.
--
-- This program and the accompanying materials are made available under the
-- terms of the Apache License, Version 2.0 which is available at
-- https://www.apache.org/licenses/LICENSE-2.0.
--
-- SPDX-License-Identifier: Apache-2.0
-- ==============================================================================
-- Idempotent database and role provisioning for Eclipse Tractus-X OSP 2.0 (ADR-0003, ADR-0005)
-- Can be executed via psql: psql -U postgres -d postgres -f init-feature-databases.sql

-- 1. Create Roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'registration') THEN
        CREATE ROLE registration WITH LOGIN PASSWORD 'registration_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'application_review') THEN
        CREATE ROLE application_review WITH LOGIN PASSWORD 'application_review_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_access') THEN
        CREATE ROLE app_access WITH LOGIN PASSWORD 'app_access_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'technical_user') THEN
        CREATE ROLE technical_user WITH LOGIN PASSWORD 'technical_user_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'company_profile') THEN
        CREATE ROLE company_profile WITH LOGIN PASSWORD 'company_profile_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'csp_connection') THEN
        CREATE ROLE csp_connection WITH LOGIN PASSWORD 'csp_connection_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'credentials') THEN
        CREATE ROLE credentials WITH LOGIN PASSWORD 'credentials_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dataspace_wallet_interface') THEN
        CREATE ROLE dataspace_wallet_interface WITH LOGIN PASSWORD 'dataspace_wallet_interface_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'connector') THEN
        CREATE ROLE connector WITH LOGIN PASSWORD 'connector_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'offers') THEN
        CREATE ROLE offers WITH LOGIN PASSWORD 'offers_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'subscriptions') THEN
        CREATE ROLE subscriptions WITH LOGIN PASSWORD 'subscriptions_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'notifications') THEN
        CREATE ROLE notifications WITH LOGIN PASSWORD 'notifications_test_pass';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'process_orchestration') THEN
        CREATE ROLE process_orchestration WITH LOGIN PASSWORD 'process_orchestration_test_pass';
    END IF;
END $$;

-- 2. Create Databases
SELECT 'CREATE DATABASE registration OWNER registration'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'registration')\gexec

SELECT 'CREATE DATABASE application_review OWNER application_review'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'application_review')\gexec

SELECT 'CREATE DATABASE app_access OWNER app_access'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'app_access')\gexec

SELECT 'CREATE DATABASE technical_user OWNER technical_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'technical_user')\gexec

SELECT 'CREATE DATABASE company_profile OWNER company_profile'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'company_profile')\gexec

SELECT 'CREATE DATABASE csp_connection OWNER csp_connection'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'csp_connection')\gexec

SELECT 'CREATE DATABASE credentials OWNER credentials'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'credentials')\gexec

SELECT 'CREATE DATABASE dataspace_wallet_interface OWNER dataspace_wallet_interface'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dataspace_wallet_interface')\gexec

SELECT 'CREATE DATABASE connector OWNER connector'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'connector')\gexec

SELECT 'CREATE DATABASE offers OWNER offers'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'offers')\gexec

SELECT 'CREATE DATABASE subscriptions OWNER subscriptions'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'subscriptions')\gexec

SELECT 'CREATE DATABASE notifications OWNER notifications'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notifications')\gexec

SELECT 'CREATE DATABASE process_orchestration OWNER process_orchestration'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'process_orchestration')\gexec

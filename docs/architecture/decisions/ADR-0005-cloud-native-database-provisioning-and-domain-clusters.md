# ADR-0005: Cloud-Native Database Provisioning & Domain Clusters

**Status:** Proposed  
**Date:** 2026-11-17  
**Authors:** Vamshidhar Reddy (@vamshidharre), Mathias Moser (@matbmoser)  
**Builds on:** [ADR-0002](ADR-0002-runtime-per-module.md) (one image, many runtimes), [ADR-0003](ADR-0003-feature-first-layout-and-runtimes.md) (feature-first layout, Decision 6 multi-database), [ADR-0004](ADR-0004-internal-boundaries-and-quality-gate.md) (internal boundaries and quality gate).

---

## 1. Context

In ADR-0002 and ADR-0003, Eclipse Tractus-X Dataspace Management Services (OSP 2.0) adopted a modular, feature-first architecture (`features/<name>/`) with single-image multi-runtime capability (`RUNTIME=<name> python -m runtimes`). All 12 hackathon modules have been refactored into distinct features.

However, moving to production deployments surfaces two critical operational challenges:

1. **Pod Topology Granularity:**
   - Deploying 13 separate microservice pods introduces excessive memory footprint, idle CPU overhead, and Kubernetes scheduler pressure for small-to-medium Onboarding Service Providers (OSPs).
   - Conversely, deploying a single monolithic pod (`installation.py`) combines unrelated failure domains (e.g., public onboarding vs. internal process orchestration).
   - An intermediate, domain-cohesive clustering topology is required.

2. **Automated Multi-Database Provisioning (ADR-0003 Decision 6):**
   - ADR-0003 mandates that each feature owns its own database, read via `<FEATURE>_DATABASE_URL` (`portal_common.database`).
   - While in-memory SQLite serves unit tests and lightweight demos, enterprise deployments require an automated, idempotent mechanism to provision dedicated PostgreSQL roles, passwords, and databases without manual DBA intervention.

---

## 2. Decision

### 1. The 5 Domain Clusters (`runtimes/`)
We establish five standard domain clusters in `runtimes/` alongside the standalone feature runtimes and the modular monolith (`installation.py`):

| Domain Runtime | Script | Encapsulated Features | Responsibility |
|---|---|---|---|
| **Onboarding** | `runtimes/onboarding.py` | `registration` (C1-M2), `application_review` (C1-M3), `company_profile` (C3-M1) | Public applicant registration, verification attestation, and reviewer approvals. |
| **Access & Security** | `runtimes/security.py` | `app_access` (C2-M2), `technical_user` (C2-M3), `credentials` (C4-M1), `dataspace_wallet_interface` (C4-M2) | Identity management, Keycloak integration, VC issuance, and BPN wallet operations. |
| **Marketplace** | `runtimes/marketplace.py` | `offers` (C8-M1), `subscriptions` (C10-M1) | Service catalog, app offers, subscriptions, and provider setup. |
| **Connectivity** | `runtimes/connectivity.py` | `csp_connection` (C3-M2), `connector` (C6-M1) | EDC connector registration and external Central Service Provider (CSP) synchronization. |
| **Operations** | `runtimes/operations.py` | `notifications` (C11-M1), `process_orchestration` (C12-M1) | Asynchronous CloudEvents inbox, long-running process workflows, and event distribution. |

### 2. Intra-Cluster vs. Inter-Cluster Communication
- **Intra-cluster:** Features within the same domain runtime invoke each other in-process via `features.<name>.interface` with zero network overhead.
- **Inter-cluster:** Cross-domain calls transit via HTTP using `MODULE_URLS` and authenticated service tokens (`svc-<module>`).
- **Asynchronous Events:** Delivered via HTTP POST to the event inbox of the `operations` runtime, where Process Orchestration (C12-M1) routes them on as the event hub ([ADR-0006](ADR-0006-process-orchestration-as-event-hub.md)); further peer inboxes in `EVENT_SINKS` are optional, all using CloudEvents (ADR-0001).

### 3. Automated Database Provisioning Lifecycle
We provide idempotent database provisioning scripts for PostgreSQL in `deploy/postgres/`:
- `deploy/postgres/init-feature-databases.sh`: Bash/psql script executed on container initialization (`/docker-entrypoint-initdb.d/`).
- `deploy/postgres/init-feature-databases.sql`: Standalone SQL DDL for DBA/operator execution.
- **Rule:** No feature may create foreign keys to tables in another database; all cross-feature referential integrity is maintained at the application/API layer.

---

## 3. Consequences

### Positive
- **Resource Efficiency:** OSPs can choose their operational density:
  - Density A: Monolith (`RUNTIME=installation`, 1 pod).
  - Density B: Domain Clusters (5 pods: `onboarding`, `security`, `marketplace`, `connectivity`, `operations`).
  - Density C: Fine-Grained Microservices (13 individual feature pods).
- **Zero Code Changes:** Moving a feature between topologies is purely an environment/deployment change (`RUNTIME` and `MODULE_URLS`).
- **Database Boundary Hardening:** Physical PostgreSQL database separation guarantees schema autonomy and prevents cross-domain data leakage.

### Trade-offs
- Deployment manifests (Docker Compose, Helm) must configure database URLs and service endpoints for the chosen topology.

---

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation

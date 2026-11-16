<!--
 Copyright (c) 2026 Contributors to the Eclipse Foundation

 See the NOTICE file(s) distributed with this work for additional
 information regarding copyright ownership.

 This program and the accompanying materials are made available under the
 terms of the Apache License, Version 2.0 which is available at
 https://www.apache.org/licenses/LICENSE-2.0.

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

 AI Disclosure: This file was entirely AI-generated.
 The AI-generated portions are made available under CC0-1.0 and not subject
 to the project's license.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: GitHub Copilot
-->

# ADR-0004: Internal boundaries and quality gate

**Status:** proposed; requires committer approval. No gate, runtime or binding instruction changes are implemented
by this record. Existing rules remain binding until their amendments are approved and implemented together.
**Related:** [PR #50](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/50) (ADR-0002 and ADR-0003),
[issue #54](https://github.com/eclipse-tractusx/dataspace-mgm-services/issues/54) and the review of
[PR #63](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/63).
**Record continuity:** this text revises the proposed ADR-0004 already integrated into `develop`, at this same
pathname. Reconcile it as one record when integrating this PR; do not retain parallel versions or allocate another
quality-policy ADR. The amendment table below makes the controller hierarchy explicit and narrows plain-database
fallback to single-feature runtimes, replacing the earlier proposal's broader test-environment exception.

## Context

The spec defines external behaviour but not enough internal structure or automatic quality enforcement.
ADR-0003 introduces readable feature packages and composable runtimes. The gate proposed in issue #54 was built
around `modules/` and a different layer vocabulary. Adopting both unchanged would create conflicting instructions.
This ADR proposes one set of internal boundaries, an incremental gate and the specific amendments needed to
ADR-0003. Architecture decisions belong here; arc42 chapters remain descriptions of the system, not a second rulebook.
Execution CI from [PR #68](https://github.com/eclipse-tractusx/dataspace-mgm-services/pull/68) and gate integration
are now present on `develop`. This revision specifies the remaining policy and verification work, not a claim that
those jobs, the spec/UI seam or branch protection have already been validated.

## Amendments to ADR-0003

Each row is a separate decision for the code owner. Retaining ADR-0003 means **amending**, not replacing or
unconditionally endorsing it. Keep ADR-0002 as the runtime-splitting record, extended by ADR-0003's feature
composition; neither record's durability follow-up is superseded by this ADR.

| Topic | Proposed position and required amendment |
|---|---|
| Feature identity | Retain readable packages, initially one per spec module. Replace `layout.feature()` deriving import paths and URLs from `ModuleSpec.name` with an explicit, unique module-ID → package-name → public-base-path mapping. Spec display-title changes must not relocate code or APIs. |
| Readable API paths | Support ADR-0003's hard switch to `/api/registration` and `/api/company-profile`, with old paths returning 404, **only as an approved breaking contract change with coordinated consumer rollout**. Do not describe it as a behaviour-preserving move. Unmigrated modules keep `/api/<module>`. See the release prerequisite below. |
| Database settings | Adopt ADR-0003 §6: `<FEATURE>_DATABASE_URL` per feature, with plain `DATABASE_URL` allowed only in a single-feature runtime. Reject ambiguous plain configuration in hybrid runtimes, including tests; multi-feature tests set per-feature URLs or use memory stores. Keep the spec naming open point; code and deployment adoption remain follow-up work, not an already completed persistence change. |
| HTTP entry points | Explicitly amend `AGENTS.md` call convention 5 for migrated features: controllers and `interface.py` are parallel entry points to own services. `router.py` only mounts controllers. Update `tools/quality/layers.py` in the same adoption PR to allow controller → service, retain router → service rejection, and keep the legacy router → interface rule. |
| Public interface | Retain explicit service re-exports in `interface.py`; delegating functions are needed only for translation. Runtime lookup and `tests/test_interfaces.py` use `getattr` and already accept re-exports. Extend `module-map` and `merge-guard` to `features/` and re-exports instead of demanding one-line wrappers. |

### Release prerequisite: paths are a spec and UI decision

FRAMEWORK 4.1 calls `/api/<module>` provisional; that is not approval to diverge from the spec's `servers` or
consumer configuration. The backend spec maintainers must approve the readable base paths and update FRAMEWORK,
the affected OpenAPI `servers` and feature mapping together. Preserve module IDs for permissions, service accounts,
Problem types, CloudEvent sources and orchestration identity: an address change does not rename those identifiers.

The UI maintainers must update the registration and company-profile adapters' base URLs, the configuration using
`CoreModuleConfig`, vendored OpenAPI copies, generated clients where affected, BFF/proxy routes, mocks and tests.
Backend maintainers must align neighbour/orchestration HTTP addressing, gateway/ingress paths, examples and release
notes. Run contract-seam checks and end-to-end registration/company-profile flows against the same pinned spec.
Verify both new routes and intentional 404s at old routes. Release the matching UI and backend together; do not
deploy the hard switch independently. If coordination is unavailable, the code owner must defer the breaking release
or approve a separately specified compatibility period rather than silently relying on old clients working.
PR #50's merge does not itself constitute spec approval or evidence that these consumers have been updated.

### Database ownership and event delivery

Use one PostgreSQL database and login role per feature, initially on one instance per installation, with no shared
tables or cross-feature repository access. Use separate deployment Secrets, feature-owned migrations and budgeted
pools. Apply feature-scoped settings to code, Helm/compose and local setup together after the spec decision.
An in-memory store may support local tests and the demo, but is not production durability; a configured database
failure must not silently fall back to memory. PR #50 now includes C2-M2's memory DAO default; verify it on the
integrated tree rather than adding a duplicate fix.

The runtime PoC already provides retry with backoff, a five-second forwarding timeout and inbox deduplication by
`source` and `id`. The missing guarantee is **durability across process restarts**, not the existence of retries or
deduplication. Retain the outbox direction recorded in chapter 9 and ADR-0002: runtime owners must implement and
test durable publication/delivery and restart recovery before claiming production-ready split runtimes.

## Proposed internal boundaries

Use ADR-0003's vocabulary; do not add a competing mandatory folder scheme:

```text
features/<readable_name>/
  __init__.py          # identity and lifecycle
  interface.py         # public spec-named steps/queries; explicit re-exports allowed
  router.py            # mounts the controller tree
  main.py              # optional standalone entry point
  controllers/         # URL segments, relative controller.py paths, parent ITEM
  services/            # business use cases
  managers/            # repositories, neighbour gateways, external adapters
  models/              # domain dataclasses and boundary schemas
  errors.py            # spec-defined Problem factories
runtimes/              # composition roots, no business rules or feature data
```

| Layer | Responsibility and allowed dependencies |
|---|---|
| Controllers | Validate HTTP input/output, authenticate and enforce available caller scope; call own services, never stores or neighbours directly. Webhooks are controllers too. |
| Public interface | Typed facade for spec-named steps and queries; call/re-export own services, with no FastAPI dependencies. |
| Services | Business rules; use own models, error factories and managers or injected ports. Never import controllers, router or runtime. |
| Managers | Repositories, neighbour gateways and external adapters; use models and shared infrastructure, never services/controllers. |
| Models and errors | No imports from services/managers. Domain dataclasses remain separate from Pydantic HTTP schemas and persistence entities. Error factories return shared `Problem` objects. |
| Runtime/lifecycle | Construct dependencies, mount routers, register callbacks, acquire/close resources. No business rules or import-time resource acquisition. |

Other features access only the target's public interface through shared neighbour transport, never its services,
managers or data. Queries use that mechanism; C12 still owns cross-feature process steps. Shared token validation,
Problem handling, settings, events and SSE stay in `portal_common`. Gateways use its addressing and service tokens.
Adapters include provider-specific and token/DID validation boundaries where applicable. Stand-ins receive callback
ports rather than importing services or reaching into stores.

Services must not assume the HTTP layer checked ownership. Check ownership wherever the caller's identity is
available. In-process neighbour queries carry query parameters, **not a person or their company scope**; do not claim
to enforce personal scope there or add a person token to the existing call convention. Internal interfaces need
explicitly defined trusted-call preconditions and tests, distinct from HTTP permission and scope tests.

Use precise Python 3.12 types, small domain dataclasses and Pydantic boundary models with spec-defined camelCase
aliases, required fields and constraints. Avoid `Any`, including nested types and aliases; narrow untrusted `object`
values before use. Preserve existing dict-based public signatures where required, using a checked JSON type.
Use Protocols for interchangeable stores/external systems, not every service or a single memory implementation.
Keep small features small: do not require empty packages or fragment code merely to satisfy size limits.

Have `mount()` derive the spec's `operationId`, rejecting duplicate/conflicting IDs and protected routes with no
token/permission dependency. Intentionally public routes must follow the reviewed contract. Require typed request
and response models; document downloads, SSE, redirects and no-content responses explicitly instead of pretending
they return JSON. Keep shared 400 Problem Details validation, not default 422, and the spec's field-error shapes.
Test actual responses as well as generated OpenAPI.

## Proposed common quality gate

Use `uv run python tools/quality/gate.py` as the single implementation, configured with `pyproject.toml`.
CI, pre-commit and opt-in agent hooks are wrappers, not separate policies. Adapt the gate integrated on `develop`
to this policy; this documentation PR supplies neither gate changes nor the proposed agent generator.

| Check | Initial acceptance policy |
|---|---|
| Ruff | Syntax, correctness, import hygiene, complexity 10 and `ANN401`; add detection for nested/aliased `Any` not caught by `ANN401`. |
| Mypy | Require typed definitions and check bodies; ratchet legacy findings. Permit only named third-party stub exceptions, not blanket ignores. |
| Size | 500 physical lines per Python file and **60 per function**, including async functions, matching the gate's `FUNCTION_LINES = 60`. |
| Architecture | Strict layer classification and dependency table for `features/` only, resolving relative imports. Reject unclassified feature files, with explicit entry-point/schema exceptions. Legacy `modules/` retain the cross-module public-interface rule in `tests/test_interfaces.py`; do not impose new layer names on their existing files. |
| Discovery | Extend module-map/merge-guard to both layouts and explicit re-exports. Require one implementation per module ID. |
| HTTP | Typed bodies/responses, spec operation IDs, documented non-JSON exceptions and shared Problem handling. |
| Contract | Compare method/path, operation ID, required fields, schemas, statuses and media types against the pinned spec. Stage parameter/security comparison as described below. Keep implemented routes distinct from spec-generated stand-in fallback routes. |
| Agent assets | Deterministic generated copies match canonical sources. |

Apply general checks to features, legacy modules, shared infrastructure, runtimes, tools and tests, with mypy scope
and exclusions explicit. Keep `ebw/` excluded as its own project. Do not apply feature layer rules to fixtures or
runtime composition. Defer repository-wide formatting to a separate agreed change.
Add locked Ruff/mypy dev dependencies: `.github/workflows/dependencies.yml` already uses
`uv export --frozen --no-dev`, so dev-only additions do not change the runtime `DEPENDENCIES` inventory.

### Contract prerequisites and matching

`tokens.require` currently declares `Header(authorization)`: generated OpenAPI has an extra header parameter and no
bearer security scheme. **Shared-platform maintainers own** replacing that declaration in `portal_common` with a
FastAPI bearer security dependency, preserving existing authentication and Problem semantics. Add tests for missing,
malformed and invalid tokens, protected/public operations and generated security requirements.
Enable full parameter/security comparison only after this prerequisite lands; do not baseline every protected
operation as a false violation. Until then, explicitly report security comparison as deferred, compare business
parameters with a narrowly documented exclusion for the synthetic authorization header, and keep runtime auth tests.
The exclusion ends when the bearer scheme lands.

Match by method and exact path template first, never first wildcard match. Where parameter spelling is normalised,
preserve literal segments and require an unambiguous match: `/notifications/count` cannot satisfy
`/notifications/{notificationId}`. Compare every operation independently, and test actual routing for dynamic routes
shadowing literals. Resolve schema references and compare meaning, not component names or key order.
Readable-base-path comparison becomes authoritative only with the approved spec/mapping; expose that dependency,
not a blanket path normalisation that hides the release seam.

### Ratchet and reproducibility

Freeze reviewed legacy findings by check/area with per-file attribution. Totals cannot grow; new files/areas start
at zero. Track stable finding identities as well as counts so one fix cannot pay for an unrelated regression.
Transfer reviewed debt explicitly on renames or module-to-feature moves, never reset or duplicate it.
`--update-baseline` only lowers allowances. CI compares with the target branch and rejects increased allowances,
removed coverage or weakened configuration except in a separate committer-approved policy change.
Resolve parallel baseline edits by recomputing on the combined tree, never selecting the larger count.
Absent specs, broken imports and subprocess failures fail the gate; they are not zero findings.

Introduce a tracked `spec.lock` containing the backend spec repository URL and one full commit ID. Shared-platform
maintainers own the local setup/CI reader: initialise or fetch into ignored `spec/`, check out that exact commit
detached, and verify `HEAD` before checks. Refuse a dirty checkout or mismatched revision without overwriting local
work. Replace `AGENTS.md`'s floating `git pull --ff-only` guidance with this setup command when implemented.
CI and local setup read the same lock, not independent refs; lock updates are reviewed PRs running all quality jobs.
Pin third-party Actions too; freeze Python 3.12 dependencies. No concrete spec revision is selected by this ADR.

### CI, local feedback and test seams

Retain three independently visible quality jobs, using the existing `.github/workflows/tests.yml` rather than a
duplicate workflow; make their required status an explicit committer action:

1. **gate:** static/architecture/OpenAPI checks and the gate's own focused pytest tests.
2. **tests:** `uv run pytest -q`, with no baseline for failing tests.
3. **demo:** `uv run python demo.py --small-iam`, which already exists; require zero exit and every expected scenario
   check. C2-M2's store default was the reported blocker; verify the merged memory default, not the flag's existence.

Run on every PR and integration push, with no filters leaving required jobs pending. Use read-only CI permissions,
no production secrets, timeouts and safe diagnostics; never run untrusted PR code under privileged
`pull_request_target`. Committers enable branch protection only once the jobs pass reproducibly.
Pre-commit calls the same gate; changed-file mode is an optimisation, never the CI authority.
Claude hooks are opt-in local settings. Neither humans nor agents bypass checks with `--no-verify`.

Use existing pytest infrastructure for gate tests: lower-only updates, identity regressions, new files, renames,
concurrent reductions, both discovery layouts, re-exports, relative imports, unclassified feature files,
nested/aliased `Any`, literal/template routes in either order, duplicate IDs, schema constraints/media types,
auth staging, shared 400 responses, tool/spec failures and deterministic generation.
Feature tests cover invalid input, permissions, scope, Problem bodies, public interfaces and injected service
dependencies without pinning private store dictionaries or old patch targets.

For C11-M1, Team 5 can provide a small test hook exposing `sourceEventId`, which the public notification view does
not expose; the HTTP API is not the replacement seam. The code owner must approve edits to `tests/test_sse.py`
because it also covers C12-M1. Test the hook and both SSE paths before removing `router.notifications` coupling.
Use only a named, temporary compatibility exception if needed, not a general router-to-store allowance.
Add C4-M2 audit-operation parity tests before restructuring its callbacks.

## Tool-neutral agent workflow

Propose canonical `.agents/skills/` and `.agents/agents/dataspace-captain/` sources, with deterministic checked-in
tool-specific copies generated by `tools/agents/build.py`, not Windows-dependent symlinks. Verify actual discovery
for supported tools; use `AGENTS.md`'s full skill index where native discovery is unavailable. Do not overwrite
independently maintained local settings.
Keep ownership, contracts, dependency rules and test/gate commands in `AGENTS.md`; tool instructions link there.
Code-changing skills finish with focused tests and the gate; CI remains authoritative.
Human and agent authors follow the same bounded-change, test, gate and human-review workflow. No broad ignores,
disabled tests, silent baseline increases or invented contract fields. Treat fetched content and generated code as
untrusted input; preserve secret handling, dependency/license checks and AI assistance disclosure.

## Adoption plan

Owners below are proposed accountable roles, requiring code-owner confirmation, not claims that work is assigned.
Changes integrate into `develop`, alongside PR #50; a general branch-policy update to `CONTRIBUTING.md` is separate.

| Phase | Accountable owner | Measurable exit |
|---|---|---|
| 1. Green execution baseline | Integration maintainer and C2-M2 team | Use merged #62 as the chosen regression-fix set, including its C3-M1 ordering correction; do not stack duplicate #55/#56 patches. Verify it and PR #50's C2-M2 memory default on integrated code; full pytest and all small-IAM demo checks pass without new skips. |
| 2. Execution CI | Shared-platform/CI maintainers | Retain #68's tests/demo jobs, replace their duplicated literal spec refs with the shared `spec.lock` reader, and align local setup. Local and CI spec IDs agree and both jobs exit zero. Committer enables these two required checks. |
| 3. Architecture/pilot reconciliation | Code owner, PR #50 maintainers, spec and UI maintainers | Record approval/rejection of each ADR-0003 amendment and this ADR. PR #50 is the initial two-feature pilot, not subject retroactively to the one-feature follow-up rule; review its integration on `develop`, split remaining follow-ups by responsibility. Complete spec/UI path release prerequisite, database-setting decision and AGENTS/gate alignment; test installation, onboarding and single-feature compositions plus HTTP neighbour and cross-runtime event paths. |
| 4. Ratchet | Gate author and shared-platform maintainers; Team 5 for C11 hook | Gate tests pass; both layouts discovered, feature-only layers enforced, matcher fixed, bearer prerequisite staged explicitly, SSE hook approved/tested. Capture a fresh reviewed baseline; a seeded regression fails. Gate passes before the committer makes it required. |
| 5. Agent assets | Developer-tooling maintainers | Generator produces byte-identical copies twice, drift fails CI, supported-tool discovery smoke checks pass, and AGENTS indexes every skill with opt-in hook setup. |
| 6. Incremental migration | Owning feature team and reviewing committer | For each follow-up PR, migrate one feature/use case, preserve contracts except separately approved changes, pass targeted/full tests, demo and gate, and lower or preserve transferred debt. Never register legacy and feature implementations together. |

The historical **1,902** findings belong to `chore/quality-gate-fastapi`; `chore/quality-gate` alone has **1,401**.
Neither is the baseline of this integrated tree: recompute after prerequisites and policy changes.
Keep relevant code under the IP-review threshold or obtain an **approved** IP review before merging, as required by
`CONTRIBUTING.md` rule 7. A request alone is insufficient; moved code still needs explicit accounting.

## Alternatives

| Alternative | Reason not selected |
|---|---|
| Keep module-ID folders as the only target | Conflicts with the feature-first direction and readable business capabilities of ADR-0003. |
| Adopt ADR-0003 and the original gate unchanged | Leaves identity/path decisions implicit and enforces conflicting layer and interface rules. |
| Apply strict new layers to every legacy file immediately | Blocks migration on unclassified legacy files instead of providing a usable ratchet. |
| Keep only aggregate finding counts | Allows a fix to conceal a different regression; per-file finding identities retain accountability. |
| Require an immediate repository-wide cleanup | Delays enforcement and mixes structural, behavioural and formatting changes. |
| Enforce with agent hooks alone | Tool-specific and bypassable; required CI must be the shared authority. |

## Consequences and pending approval

One vocabulary and incremental enforcement reduce divergence without requiring microservices or a big-bang rewrite.
They add generator/gate maintenance and require coordinated changes to instructions, discovery and shared security.
Readable paths are deliberately breaking; feature-scoped database settings require deployment and spec agreement.
The code owner must approve the amendment table, initial limits, baseline policy, phase owners and release gates.
Production durability remains ADR-0002's follow-up. This record neither claims green CI nor closes issue #54;
implementation and verification remain separate changes.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- AI Disclosure: This proposal was AI-generated; the AI-generated portions are made available under CC0-1.0.
- SPDX-License-Identifier: CC-BY-4.0 AND CC0-1.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Assisted-By: GitHub Copilot
- Source URL: <https://github.com/eclipse-tractusx/dataspace-mgm-services>

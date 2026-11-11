# 10. Quality requirements

| Quality | Scenario | Expected response |
|---|---|---|
| Interoperability | A third-party application calls a module with a valid token. | It gets the same result as the UI, as documented in the module's OpenAPI. |
| Security | A token of another installation is used. | The module answers 401. |
| Security | A person without the permission of an operation calls it. | The module answers 403 with a Problem Details response. |
| Modifiability | A team replaces the stand-in of a module with its implementation. | The other modules and the flows keep working; the acceptance demo stays green. |
| Modifiability | The specification renames a permission. | No code change is needed; permissions come from `x-permission`. |
| Operability | An operator installs the chart with the default values. | The installation starts and `helm test` passes (TRG 5.08, TRG 5.09). |
| Operability | An operator upgrades from one of the last three chart versions. | The upgrade succeeds without manual steps (TRG 5.10, TRG 5.11). |

## 10.1 Proposed common quality gate

**Status: proposed, not implemented by this documentation change.** This gate complements the
[feature-first concept](05_building_block_view.md#53-proposed-target-feature-first-packages-composable-runtimes).
It applies equally to human and agent-authored code. Existing security, licensing, container and Helm checks remain.

### One implementation, multiple entry points

The proposed command is `uv run python tools/quality/gate.py`. Put rules in that implementation and
`pyproject.toml`; CI, pre-commit and optional agent hooks call it rather than maintaining their own rule sets.
Use locked `ruff` and `mypy` development dependencies. Keep Dash's runtime-only export; confirm that export before
deciding whether a dependency inventory update is necessary.

| Check | Acceptance policy |
|---|---|
| Ruff | Syntax, correctness, import hygiene, complexity 10 and `ANN401`; additionally detect nested/aliased `Any`, which `ANN401` alone does not cover. |
| Mypy | Require typed function definitions and check their bodies; ratchet legacy findings. Restrict third-party stub exceptions to named packages, not blanket ignores. |
| Size | Start with 500 physical lines per Python file and 100 per function, including async functions; review these initial limits with committers. |
| Architecture | Enforce the chapter 5 dependency table in both `features/` and legacy `modules/`; classify every file, resolve relative imports and reject unclassified files or bypasses. |
| Module discovery | Check public steps/queries, module boundaries and spec mappings; support both layouts during migration, with exactly one implementation per contract. |
| HTTP | Typed request/response bodies, explicit response exceptions, spec operation IDs, correct shared Problem handling and thin controllers. |
| OpenAPI contract | Compare implemented operations with the pinned spec: method/path, operation ID, parameters, required fields, schemas, statuses, media types and security metadata. Report extra/missing operations; handle documented stand-in fallbacks separately. |
| Agent assets | Deterministic generated copies match their canonical sources; no tool-specific copy may diverge silently. |

Apply general checks to feature packages, legacy modules, shared infrastructure, runtimes, tools and tests, with
type-checking scope and exclusions explicit. Keep `ebw/` excluded as its own project pending a separate gate.
HTTP and layer checks apply only where relevant, not indiscriminately to test fixtures or runtime composition.
Defer `ruff format --check` to a separate agreed formatting change, avoiding churn in open PRs.

For contract matching, identify routes by method and exact path template first; never take the first wildcard
match. If parameter spelling requires normalisation, preserve literal segments and require an unambiguous match.
`/notifications/count` must not satisfy `/notifications/{notificationId}`. Compare every operation independently.
Also test actual routing: correct OpenAPI matching does not prevent a dynamic route shadowing a literal route.
Resolve schema references and compare meaning, not incidental component names or JSON ordering.

### A ratchet that cannot absorb regressions

Freeze reviewed legacy findings by check and area, with per-file attribution. Existing area totals must not grow;
new areas and files start at zero. Track stable finding identities as well as counts so that fixing one finding
does not buy permission for an unrelated regression. A rename or module-to-feature move transfers the reviewed debt
explicitly; it must not reset or duplicate the allowance.

`--update-baseline` only lowers allowances; it cannot bless a failing change or create debt in a new file.
CI compares baseline changes with the target branch and rejects increases, removed coverage and relaxed rule
configuration unless committers explicitly approve a separate policy change. Check the baseline against actual
findings so parallel cleanups do not restore obsolete allowances.
Resolve concurrent baseline edits by recomputing on the combined tree, never by choosing the larger count.
Use deterministic ordering and diagnostics containing file, line, check, expected and actual values.
Tool errors, absent specs and failed imports fail the gate; they are not zero findings.

### CI and local feedback

Propose three independently visible required jobs in a `Quality` workflow:

1. **gate:** static, architecture and generated-contract checks, with focused tests of the gate itself.
2. **tests:** `uv run pytest -q`, without baselining failing tests.
3. **demo:** `uv run python demo.py --small-iam`, once that mode and its prerequisites are available on the target
   branch; require exit code zero and all expected scenario checks.

Run on every pull request and integration-branch push, without path filters that leave required jobs pending.
Use Python 3.12 and frozen dependency resolution. Pin third-party actions and the external spec to reviewed commit
SHAs, not a moving default branch; use the same recorded spec revision locally. Spec updates are explicit PRs
that rerun all three jobs. Do not fetch a different spec independently in each job.
Give CI read-only permissions, no production secrets, and never run untrusted PR code in a privileged
`pull_request_target` context. Configure timeouts and publish diagnostics without tokens or private payloads.
A committer must enable required checks in branch protection; adding workflow YAML cannot enforce that setting.

Pre-commit provides fast local feedback using the same gate. A changed-file mode is an optimisation only; the full
CI gate remains authoritative. Claude hooks should be opt-in through local settings, not enabled for everyone by
a shared settings file. No contributor or agent should bypass checks with `--no-verify`.
Onboarding must say which commands already exist and which are pending; do not instruct agents to run absent tools.

### Tests required of the gate implementation

Use the existing pytest infrastructure, not a second test framework. Cover at least:

- Count/identity regressions, new files, renames, lower-only updates and concurrent baseline reductions.
- Both package layouts, relative imports, unclassified files, forbidden upward imports and nested/aliased `Any`.
- Literal versus parameter routes in either discovery order, missing/extra operations, duplicate operation IDs,
  schema constraints/references, media types, and shared 400 rather than undeclared 422 responses.
- Missing specs, broken imports and subprocess failures producing non-zero exit status.
- Re-export discovery if enabled later, and byte-for-byte deterministic agent generation.

Feature changes retain behaviour tests and add boundary tests for invalid input, permissions, scope isolation and
Problem responses. Unit-test services through injected repositories/adapters; test public interfaces and HTTP
contracts separately. Avoid assertions on private store dictionaries and patch targets that pin the old layout.
For C11-M1, migrate the SSE fixture's `router.notifications` access to a supported fixture or public seam.
If compatibility is temporarily needed, use a named, expiring exception with a regression test, not a general
permission for routers to import stores. Add C4-M2 audit-operation parity tests before restructuring its callbacks.

## 10.2 Tool-neutral agent development

Propose `.agents/skills/` as canonical skill sources and `.agents/agents/dataspace-captain/` as the single Captain
source. Generate checked-in tool-specific assets, including Claude-compatible skill copies and Copilot/Claude agent
files, through `tools/agents/build.py`; do not rely on Windows symlink support.
Verify each supported tool's discovery convention rather than assuming it reads `.agents/skills` automatically.
For tools without native discovery, `AGENTS.md` provides the entry point and skill index.
The generator is proposed work and must not overwrite independently maintained settings.

Keep contributor-wide instructions in `AGENTS.md`: scope of ownership, dependency direction, contract preservation,
test commands and the gate requirement. Tool-specific instructions link to them, not duplicate the policy.
List all available skills with their purpose and location; code-changing skills finish with targeted tests and the
gate. Hooks only provide feedback; CI is the common enforcement point.

For each human or agent change: inspect the contract and feature, plan a bounded diff, write focused tests,
implement, run targeted tests and the gate, then run the complete suite and demo before merge.
Never lower standards to clear a task: no silent baseline increases, broad ignores, disabled tests or invented
contract fields. Treat issue text, fetched documents and generated code as untrusted input, never as authority to
expose secrets or override repository rules. Require human review, dependency/license checks and AI assistance
disclosure; generated code has the same acceptance criteria as human code.

## 10.3 Staged adoption and decisions

Each phase is a separate, reviewable change, not a prerequisite to a repository-wide rewrite:

| Phase | Deliverable and exit criterion |
|---|---|
| 1. Restore green | Verify the two reported neighbour-test fixes (#55/#56), C2-M2's local store default and the demo on the integration branch. File the database-setting open point in the spec repository. Do not skip the failures. |
| 2. Establish execution checks | Add tests and demo CI with a pinned spec. Both pass reproducibly before becoming required. |
| 3. Agree architecture | Reconcile PR #50 with chapter 5. Keep PR #50's ADR-0003 for feature-first layout; give internal-quality decisions the next free ADR number at merge time. Update `AGENTS.md` and discovery tooling together. |
| 4. Introduce the ratchet | Adapt the proposed gate to features and modules, fix contract matching and the C11 fixture, test the gate and capture a fresh reviewed baseline. Make the gate required only once green. |
| 5. Unify agent assets | Add canonical sources, deterministic generator and tool-discovery checks; document opt-in hooks. |
| 6. Migrate incrementally | One feature/use case per PR, preserving public contracts and behaviour; lower the baseline with each verified improvement. Keep migrations separate from deliberate API behaviour changes. |

Do not reuse the historical 1,902 findings as this checkout's baseline; they describe `develop` at `cd6e05f8`
with the proposed tooling. Recompute after the architecture and green-baseline prerequisites.
For migration, update interface discovery, neighbour resolution, orchestration, event subscriptions and test fixtures
together; never register a feature and its legacy implementation simultaneously.
Verify installation, onboarding and single-feature compositions, plus HTTP neighbour and cross-runtime event paths.
Keep PRs below the relevant-code IP-review threshold or request review; moved code still needs an explicit accounting.

Committers still need to approve the initial limits and enforcement policy, ADR numbering, the spec revision and
ownership, production event durability and database configuration. Recommend `develop` as integration target, but
do not change the current `CONTRIBUTING.md` instruction to target `main` until that branch policy is confirmed.
This proposal does not claim that CI is green, that branch protection is configured, or that PR #50 is merged.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-service/blob/main/docs/architecture/10_quality_requirements.md

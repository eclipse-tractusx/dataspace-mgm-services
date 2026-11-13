# Interface documentation

The Dataspace Management Service exposes one HTTP interface per module, described in OpenAPI 3.1 (TRG 1.08).

## OpenAPI per module

Each module of the specification has an `openapi.yaml` that is the contract for the UI, for third parties and for calls
between modules in the same process. The module specifications (until they are moved to Eclipse Tractus-X) are in
[tx-arena-events/portal-backend-spec](https://github.com/tx-arena-events/portal-backend-spec):

| Module | Base path |
|---|---|
| C1-M2 Registration | `/api/registration` (migrated feature, ADR-0003) |
| C1-M3 Application Review | `/api/c1-m3` |
| C2-M2 Users and App Access | `/api/c2-m2` |
| C2-M3 Technical Users | `/api/c2-m3` |
| C3-M1 Company Profile | `/api/company-profile` (migrated feature, ADR-0003) |
| C3-M2 CSP Connection | `/api/c3-m2` |
| C4-M1 Credentials | `/api/c4-m1` |
| C4-M2 Dataspace Wallet Interface | `/api/c4-m2` |
| C6-M1 Connectors | `/api/c6-m1` |
| C8-M1 Offers | `/api/c8-m1` |
| C10-M1 Subscriptions | `/api/c10-m1` |
| C11-M1 Notifications | `/api/c11-m1` |
| C12-M1 Process Orchestration | `/api/c12-m1` |

A migrated feature (`features/<name>/`, ADR-0003) is served under its readable name instead of the spec id; the old
path answers 404. Every other module keeps `/api/<module>` of its `openapi.yaml` until it migrates.

Conventions that apply to all modules (FRAMEWORK 4.1): JSON fields in camelCase, times in ISO 8601 UTC, IDs as UUID,
paginated lists with `page`/`size`, steps for Process Orchestration under `/steps/...`, queries for other modules under
`/internal/...`, Server-Sent Events under `.../events`, the extensions `x-permission` and `x-permission-scope`.

## OpenAPI of the installation

A running installation serves its combined interface at `/openapi.json` and an interactive Swagger UI at `/docs`.
For every release, the combined document is stored as `openAPI.yaml` in this folder and referenced in the
[`.tractusx`](../../.tractusx) metadata file (key `openApiSpecs`), so that it is published on the
[Tractus-X API hub](https://eclipse-tractusx.github.io/api-hub/). The first `openAPI.yaml` is added together with the
source code of the service. It is exported from the application with:

```shell
uv run python -c "import yaml; from scaffold.app import create_app; print(yaml.safe_dump(create_app().openapi(), sort_keys=False))" > docs/api/openAPI.yaml
```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-service/blob/main/docs/api/README.md

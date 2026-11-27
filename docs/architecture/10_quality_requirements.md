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

Quality gate requirements, static analysis (ruff, mypy), layer boundary enforcement, and OpenAPI contract checking are defined in [ADR-0004](decisions/ADR-0004-internal-boundaries-and-quality-gate.md) and executed via `tools/quality/gate.py`.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-service/blob/main/docs/architecture/10_quality_requirements.md

# Installation

This guide installs the Eclipse Tractus-X **Dataspace Management** (new portal) of one onboarding service provider (OSP)
with the product Helm chart [`charts/dataspace-mgm`](charts/dataspace-mgm). The chart contains both components of the
product, the Dataspace Management Service (backend) and the [Dataspace Management UI](https://github.com/eclipse-tractusx/dataspace-mgm-ui).

- [Prerequisites](#prerequisites)
- [Install the Helm chart from the Helm chart repository](#install-the-helm-chart-from-the-helm-chart-repository)
- [Use the Helm chart as a dependency of your own Helm chart](#use-the-helm-chart-as-a-dependency-of-your-own-helm-chart)
- [Configure the Helm chart](#configure-the-helm-chart)
- [Verify the installation](#verify-the-installation)
- [Upgrade](#upgrade)
- [Uninstall](#uninstall)
- [Local development](#local-development)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Kubernetes 1.29+ and `kubectl`
- [Helm](https://helm.sh/docs/intro/install/) 3.8.0+
- An ingress controller, if the UI and the API are exposed through an ingress
- For an operated installation: a Portal IAM (Keycloak, realm of C2-M5) and access to the core services of a CSP,
  see the [admin guide](docs/admin/README.md)

## Install the Helm chart from the Helm chart repository

```shell
# 1. Add the Tractus-X Helm chart repository
helm repo add tractusx-dev https://eclipse-tractusx.github.io/charts/dev
helm repo update

# 2. Install the chart (demo installation with the default values)
helm install dataspace-mgm tractusx-dev/dataspace-mgm --namespace dataspace-mgm --create-namespace
```

The released charts of this product are also available from its own chart repository:

```shell
helm repo add dataspace-mgm https://eclipse-tractusx.github.io/dataspace-mgm-service
```

From a checkout of this repository:

```shell
helm install dataspace-mgm charts/dataspace-mgm --namespace dataspace-mgm --create-namespace
```

## Use the Helm chart as a dependency of your own Helm chart

```yaml
dependencies:
  - name: dataspace-mgm
    repository: https://eclipse-tractusx.github.io/charts/dev
    version: 0.1.x
```

## Configure the Helm chart

The default values start a self-contained **demo installation** (OSP A of the hackathon scenario, in-memory Portal IAM,
built-in CSP stand-in, test doubles). For an operated installation, set at least `backend.testTools=false`, the Portal IAM
(`backend.iam.*`), the CSP (`backend.csp.url`), the installation settings (`backend.installation.*`), the secrets and the
ingresses. The [admin guide](docs/admin/README.md) has a complete example; the [chart README](charts/dataspace-mgm/README.md)
lists every value.

```shell
helm install dataspace-mgm tractusx-dev/dataspace-mgm --namespace dataspace-mgm --create-namespace -f my-values.yaml
```

## Verify the installation

```shell
kubectl get pods --namespace dataspace-mgm
helm test dataspace-mgm --namespace dataspace-mgm

# Without ingress: open the API documentation and the UI locally
kubectl --namespace dataspace-mgm port-forward svc/dataspace-mgm-backend 8000:8000
#   -> http://localhost:8000/docs and http://localhost:8000/health
kubectl --namespace dataspace-mgm port-forward svc/dataspace-mgm-frontend 8080:8080
#   -> http://localhost:8080
```

## Upgrade

```shell
helm repo update
helm upgrade dataspace-mgm tractusx-dev/dataspace-mgm --namespace dataspace-mgm -f my-values.yaml
```

Read the [CHANGELOG](CHANGELOG.md) before an upgrade.

## Uninstall

```shell
helm uninstall dataspace-mgm --namespace dataspace-mgm
kubectl delete namespace dataspace-mgm
```

## Local development

Prerequisites: [uv](https://docs.astral.sh/uv/), git and Docker with Compose.

```shell
uv sync                    # Python 3.12 and the dependencies from uv.lock
uv run pytest -q           # all tests
docker compose up -d       # test Portal IAM (Keycloak, C2-M5)
uv run uvicorn --factory scaffold.app:create_app --port 8000
#   -> http://localhost:8000/docs
```

Databases: all modules of an installation run in one process, so each module with a database reads its own variable,
`C2_M2_DATABASE_URL` (optional for C2-M2, otherwise in memory; `APP_ACCESS_DATABASE_URL` also works) and `C3_M1_DATABASE_URL` (optional, otherwise in memory). Do not set
`DATABASE_URL` in an installation: a runtime serving multiple features refuses to start when `DATABASE_URL` is set
without dedicated variables configured for each feature (ADR-0003 decision 6, FRAMEWORK 4.9).

```shell
docker run -d --name c2m2-db -e POSTGRES_PASSWORD=local-test-only -e POSTGRES_DB=c2_m2 -p 5432:5432 postgres:16
export C2_M2_DATABASE_URL=postgresql://postgres:local-test-only@localhost:5432/c2_m2
uv run python demo.py
```

Build and run the container image:

```shell
docker build -t tractusx/dataspace-mgm-service:local .
docker run --rm -p 8000:8000 --read-only --tmpfs /tmp tractusx/dataspace-mgm-service:local
```

## Troubleshooting

| Problem | Solution |
|---|---|
| The backend pod does not get ready | `kubectl logs deploy/dataspace-mgm-backend`. A missing installation setting (`ospId`, `ospName`, `ospCompanyId`) stops the start-up with a message naming the setting. |
| Every call answers 401 | The token is not from the Portal IAM of this installation: check `backend.iam.url`, `backend.iam.realm` and `backend.iam.issuer`. |
| The UI shows "The portal could not start" | `/config.json` is missing or invalid: check `frontend.config.apiBaseUrl` (must be a URL). |
| The browser blocks calls to the API | UI and API must share the registrable domain, and the API must allow the UI origin in CORS with credentials. |
| `helm test` fails | `helm test dataspace-mgm --logs` shows the output of the test pods. |

For further help, contact the project on the [Tractus-X dev mailing list](https://accounts.eclipse.org/mailing-list/tractusx-dev).

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/dataspace-mgm-service/blob/main/INSTALL.md

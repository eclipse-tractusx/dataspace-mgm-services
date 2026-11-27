<!--
Copyright (c) 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# ebw-stack

Helm chart of the EBW stack for demos and tests with real wallets: the **EBW-Connector** (reference implementation of
C5-M1), a **Business Wallet** in the browser and the **test tools** (test issuer, trust list, demo portal).

It is not a product chart. The stack holds a test issuer that gives a PID to everyone who asks, and its keys are
test keys. Install it next to a portal that is meant for demos, never next to one that is operated.

One pod runs the three services as three containers. They share one volume, because the EBW-Connector reads the
public key of the trust list from the test tools, and there is one instance, because running transactions are in memory.

## What you need

- Kubernetes 1.29+, Helm 3.8.0+ and an ingress controller.
- **Three public host names** that point at the ingress controller, one per service.
- **A certificate that phones trust** for these names (for example from cert-manager with Let's Encrypt). A wallet app
  on a phone does not open an address with a self-signed certificate.
- The image, built from `ebw/Dockerfile` and pushed to a registry the cluster can pull from. There is no public image.
- A volume of 1 Gi (`ReadWriteOnce`).

## Image

In the folder `ebw/`:

```bash
docker build --platform linux/amd64 -t <registry>/ebw-stack:0.3.0 .
docker push <registry>/ebw-stack:0.3.0
```

`--platform` names the architecture of the cluster nodes; leave it out when you build on the same architecture.

## Install

A values file with the names of your environment:

```yaml
image:
  repository: <registry>/ebw-stack
  tag: "0.3.0"
connector:
  host: connector.ebw.example.org
businessWallet:
  host: business-wallet.ebw.example.org
testTools:
  host: test-tools.ebw.example.org
ingress:
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
    - secretName: ebw-stack-tls
      hosts:
        - connector.ebw.example.org
        - business-wallet.ebw.example.org
        - test-tools.ebw.example.org
```

```bash
helm upgrade --install ebw-stack ebw/charts/ebw-stack -n <namespace> -f my-values.yaml
kubectl -n <namespace> rollout status deployment/ebw-stack
```

Check from outside the cluster:

```bash
curl -s https://connector.ebw.example.org/.well-known/openid-configuration   # "issuer" is the public address
curl -s https://test-tools.ebw.example.org/trust-list.json                   # the test issuer is listed
curl -s -o /dev/null -w '%{http_code}\n' https://business-wallet.ebw.example.org/   # 200
```

Then open the test tools in a browser, issue a PID and take it into a wallet app on a phone.

## Connecting a portal

The EBW-Connector only answers clients it knows (C5-M1 6.8). The demo portal and the Business Wallet of the stack are
registered by the chart. Add the clients of a portal in `connector.clients`:

```yaml
connector:
  clients:
    # the Portal IAM (Keycloak), for the sign-in with the wallet
    - clientId: portal-iam
      name: Portal IAM of OSP A
      jwksUri: https://iam.example.org/auth/realms/CX-Central/protocol/openid-connect/certs
      redirectUris: [https://iam.example.org/auth/realms/CX-Central/broker/ebw-connector/endpoint]
      scopes: [openid, profile]
      page: {theme: tractusx, brand: Eclipse Tractus-X, tagline: Dataspace Management}
    # the server part of the portal UI, for the wallet step of the onboarding and of joining with a mandate
    - clientId: osp-a-ui
      name: The portal of OSP A
      jwksUri: https://portal.example.org/ebw/jwks
      redirectUris: [https://portal.example.org/ebw/callback]
      scopes: [openid, profile, representation, company, attestation]
      page: {theme: tractusx, brand: Eclipse Tractus-X, tagline: Dataspace Management}
```

The EBW-Connector fetches each `jwksUri` itself, so the pod must reach these addresses. Where it cannot, put the keys
into the entry as `jwks` instead. A changed list arrives without a restart, about a minute after `helm upgrade`.

The other side needs the public address of the EBW-Connector:

| Where | Setting |
|---|---|
| Portal IAM, identity provider `ebw-connector` | issuer `https://<connector>`, authorization `…/authorize`, token `…/token`, keys `…/jwks` |
| Backend (C1-M2, C2-M2) | `ATTESTATION_ISSUER=https://<connector>`, `ATTESTATION_JWKS_URL=https://<connector>/jwks`, `ATTESTATION_CLIENT_IDS=osp-a-ui` |
| Server part of the portal UI | `BFF_EBW_ISSUER_URL=https://<connector>`, `BFF_EBW_CLIENT_ID=osp-a-ui`, `BFF_EBW_KEY_FILE` |

## Values

| Key | Default | Description |
|---|---|---|
| `image.repository`, `image.tag` | `ebw-stack`, chart `appVersion` | Image of the three containers |
| `imagePullSecrets` | `[]` | Pull secrets of a private registry |
| `publicScheme` | `https` | Scheme of the public addresses; `http` only for tests inside a cluster |
| `connector.host`, `businessWallet.host`, `testTools.host` | `*.ebw.example.org` | Public host names |
| `connector.clients` | `[]` | Further clients of the EBW-Connector |
| `connector.env`, `businessWallet.env`, `testTools.env` | | Further settings of one service |
| `responseMode` | `direct_post.jwt` | How a wallet returns its answer; `direct_post` for wallets without encryption |
| `env`, `extraEnv`, `extraVolumes`, `extraVolumeMounts` | | For all three containers |
| `hostAliases` | `[]` | Host names the pod resolves itself (see below) |
| `ingress.enabled`, `ingress.className`, `ingress.annotations`, `ingress.tls` | `true`, `nginx`, `{}`, `[]` | One ingress with the three host names |
| `persistence.enabled`, `persistence.existingClaim`, `persistence.storageClass`, `persistence.size` | `true`, `""`, `""`, `1Gi` | Volume with keys and data |
| `resources` | 50m / 192Mi | Per container |

## Good to know

- **Keys live on the volume.** If it is lost, or with `persistence.enabled=false` after every restart, the stack
  creates new keys: the credentials in the wallets and the company credential of the Business Wallet stop working and
  have to be fetched again. `helm uninstall` removes a volume that the chart created.
- **The services call each other through their public addresses** (status lists, keys of the clients, token calls).
  If the cluster cannot reach its own public addresses from inside, name the IP address of the ingress controller in
  `hostAliases` for the three host names.
- **Without `https`** (`publicScheme: http`, a test inside a cluster) the EBW-Connector does not accept the status lists:
  it reads them over `https` or from `localhost` only. Serve them inside the pod then:
  `testTools.env.STATUS_BASE_URL=http://localhost:8079` and `businessWallet.env.STATUS_BASE_URL=http://localhost:8078`.
- **A private certificate authority:** mount a bundle with its certificate with `extraVolumes` and `extraVolumeMounts` and
  set `env.SSL_CERT_FILE` to the file; the services then trust only the certificates of that bundle. Phones still need
  to trust the certificate of the public addresses.
- **The wallet request is signed with a self-signed certificate** for the host name of the EBW-Connector. For another
  one, mount the chain and set `connector.env.REQUEST_CERT_FILE`; the certificate must belong to the key
  `connector/keys/signing.pem` on the volume.
- **The stack is open.** Everyone who knows the addresses can fetch test credentials, set up an empty Business Wallet
  and reset the Business Wallet without signing in. Keep the addresses to the people of the demo and take the stack down
  afterwards.
- **Starting from zero:** delete the volume claim and restart the pod, or reset the Business Wallet on its page.

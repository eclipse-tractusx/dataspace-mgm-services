# Open Questions

1. **IssuerService Admin API version and base path.** The client currently defaults to `v1beta` and constructs `/api/admin/{version}/participants/{participantId}` unless `ISSUER_SERVICE_ADMIN_URL` already contains `/participants/`. Confirm these paths against the deployed IssuerService version; public IdentityHub API documentation may use a different version/path.
2. **IssuerService Admin API authentication.** The client currently sends `ISSUER_SERVICE_API_KEY` as `x-api-key`. Confirm whether the target deployment supports this or requires OAuth2 for its Admin API.
3. **C4-M2 split-runtime authorization.** When C4-M2 is remote, `portal_common.neighbours` calls it as `c4-m1` using the `svc-c4-m1` service token. Confirm the deployment provisions the service account, its query permission, a production `SERVICE_CLIENT_SECRET`, Portal IAM connectivity, and a `C4_M2_URL` or `MODULE_URLS` entry.
4. **Holder listing semantics.** `get_holders()` sends an empty `QuerySpec` and does not paginate. Confirm the deployed IssuerService default query limit and whether this operation should support pagination.
5. **Issuer-side revocation.** This feature does not revoke credentials. C4-M1 currently needs the IssuerService credential ID to use the Admin API revocation endpoint; confirm that C4-M1 remains the owner and how it obtains/correlates that ID if direct issuer revocation is needed.
6. **Issuance completion.** The IdentityHub endpoint response only acknowledges the wallet request. Confirm that C4-M1's existing callback/status mechanism remains the sole source of portal issuance completion; this feature does not poll IdentityHub or IssuerService.
7. **Standalone API contract.** This feature has no assigned spec module ID or committed OpenAPI contract. Confirm whether it remains a private integration service or will receive a spec-backed contract before other consumers depend on its HTTP API.

See [KNOWN-KNOWNS.md](KNOWN-KNOWNS.md) for confirmed behavior, constraints, and current risks.

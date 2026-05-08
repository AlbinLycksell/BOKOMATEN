# Auth

## Production: NextAuth + Google → backend JWKS

```
Browser → NextAuth (web) → Google OAuth → JWT cookie + JWKS endpoint
                                              │
                                              ▼
                              Backend reads `Authorization: Bearer <jwt>`,
                              verifies via JWKS, binds `firma_id` claim
                              into the request scope (`TenantMiddleware`).
```

- NextAuth route: `web/app/api/auth/[...nextauth]/route.ts`
- Backend verification: `backend/src/svarsa/core/auth.py`
- Middleware that binds the firma context: `backend/src/svarsa/core/middleware.py`

The `firma_id` claim is stamped by the NextAuth `jwt` callback. Production extends this to look up the user's firma from a `users` table — current implementation hard-codes the demo firma until the multi-firma data model lands.

## Required env

| Var | Web | Backend | Source |
|---|---|---|---|
| `NEXTAUTH_URL` | ✓ | — | `https://app.svarsa.se` |
| `NEXTAUTH_SECRET` | ✓ | — | `openssl rand -base64 32` |
| `GOOGLE_CLIENT_ID` | ✓ | — | GCP Credentials |
| `GOOGLE_CLIENT_SECRET` | ✓ | — | GCP Credentials |
| `SVARSA_AUTH_MODE` | — | ✓ | `jwks` in prod, `dev_header` in dev |
| `SVARSA_AUTH_JWKS_URL` | — | ✓ | `https://app.svarsa.se/api/auth/jwks` |
| `SVARSA_AUTH_AUDIENCE` | — | ✓ | `svarsa-backend` |
| `SVARSA_AUTH_ISSUER` | — | ✓ | `https://app.svarsa.se` |

## Dev: header-based shim

`SVARSA_AUTH_MODE=dev_header` (default in dev). The backend reads `X-Firma-Id` and binds it. Convenient for local testing without a full OAuth round-trip. Production rejects this path (the middleware refuses to honor `X-Firma-Id` when `auth_mode=jwks`).

## Internal calls (Bridge → Backend)

The Realtime Bridge calls `POST /api/tools/dispatch` over the VPC connector. Two protections:

- `X-Internal-Token` header (verified against `Settings.bridge_internal_token`).
- Cloud Run service-to-service authentication (the bridge's service account has `roles/run.invoker` on the backend service).

The bridge passes the firma's `X-Firma-Id` directly — there's no end-user JWT in the loop.

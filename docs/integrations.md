# Integrations setup guide

Each external system is wired through a typed client under `backend/src/svarsa/integrations/`. This doc tells you how to enable each one.

## 46elks (telephony + SMS)

### Voice (inbound calls)

1. 46elks dashboard → Numbers → click your Swedish number → "Voice Settings".
2. Set "URL when called" to `https://app.svarsa.se/api/integrations/elks/voice/inbound` (HTTP POST).
3. Verify with a test call to your number — you should land in the bridge logs within 1–2 s.

### SMS

1. 46elks dashboard → SMS → Senders → Add sender — submit firma name and a permission letter.
2. Wait 3–5 business days for verification.
3. Set `SVARSA_ELKS_DEFAULT_SENDER_ID` for the platform default (`Svarsa`).
4. Per-firma sender ids: stored in `Firma.settings` (UI: settings page → SMS sender) and passed via `send_sms(sender_id=...)`.

### Env

| Var | Purpose |
|---|---|
| `SVARSA_ELKS_API_USERNAME` | API auth username |
| `SVARSA_ELKS_API_PASSWORD` | API auth password |
| `SVARSA_ELKS_DEFAULT_SENDER_ID` | Platform fallback sender id |
| `SVARSA_ELKS_WEBHOOK_SECRET` | Reserved for HMAC verification (P15+) |

## Vertex AI (Gemini Live)

1. GCP console → APIs → enable `aiplatform.googleapis.com`.
2. Grant `roles/aiplatform.user` on each Cloud Run service account (Terraform does this via `workload_identity` module).
3. Set `SVARSA_GEMINI_PROVIDER=vertex` + `SVARSA_VERTEX_PROJECT=<id>` + `SVARSA_VERTEX_LOCATION=europe-west4` in Cloud Run env.

The `google-genai` client picks up Application Default Credentials from the service account.

## Fortnox (planned)

Outline; full client lands with Step 7 of next-steps.

1. https://developer.fortnox.se/ → Sign up. Approval ~1–3 business days.
2. Create OAuth application → redirect URL `https://app.svarsa.se/api/integrations/fortnox/callback`.
3. Scopes: `customer`, `bookkeeping`, `invoice` (read), `connectfile`.
4. Per-firma OAuth tokens encrypted with a tenant DEK; stored in `Integration.sync_state`.
5. Owner connects from Settings → Integrations → "Anslut Fortnox".

## Hantverksdata Next (planned)

1. Email `partners@hantverksdata.se` to start partneravtal (~2–4 months).
2. On approval: API credentials stored in Secret Manager + per-tenant DEK-encrypted refresh tokens in Postgres.

## Visma eEkonomi (planned)

Same shape as Fortnox. https://developer.visma.com/.

## Google Calendar (planned)

Same OAuth client as auth (Step 3) + add `https://www.googleapis.com/auth/calendar` scope. Bidirectional CalDAV sync.

## Bolagsverket (planned)

Public org-number lookup. No auth. Cached 7 days in Redis (when Memorystore lands).

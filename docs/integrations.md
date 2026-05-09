# Integrations setup guide

Each external system is wired through a typed client under `backend/src/switchboard/integrations/`. Per-tenant OAuth refresh tokens are KMS-encrypted at rest and stored in `Integration.sync_state`.

## 46elks (telephony + SMS)

### Voice — pcm_24000 streaming

The bridge implements the official 46elks Voice Streaming protocol (https://46elks.fi/tutorials/real-time-two-way-voice-calls-with-websocket).

1. 46elks dashboard → Numbers → your Swedish number → Voice Settings.
2. "URL when called" → `https://app.switchboard.se/api/integrations/elks/voice/inbound`.
3. Webhook returns `{"connect":"wss://bridge.switchboard.se/ws/bridge/{firma}/{call}"}` and 46elks opens that WebSocket.
4. Audio flows in JSON-typed messages (`{"t":"audio","data":"<base64 PCM 24kHz mono int16>"}`). Bridge handles `hello` / `audio` / `sync` / `bye` per the protocol.

### SMS — per-firma verified sender ids

1. 46elks dashboard → SMS → Senders → Add sender. Submit firma name + org-nummer + permission letter.
2. Wait 3–5 business days for verification.
3. Owner edits the sender id from Settings → Integrationer → SMS sender. Backend sends with that id only when `Firma.settings.sms_sender_id_verified` is true; otherwise falls back to platform `Switchboard`.

### Env

| Var | Purpose |
|---|---|
| `SWITCHBOARD_ELKS_API_USERNAME` / `SWITCHBOARD_ELKS_API_PASSWORD` | 46elks API auth |
| `SWITCHBOARD_ELKS_DEFAULT_SENDER_ID` | Platform fallback sender id (default `Switchboard`) |
| `SWITCHBOARD_ELKS_WEBHOOK_SECRET` | Reserved for HMAC verification |

## Vertex AI (Gemini Live)

1. GCP console → APIs → enable `aiplatform.googleapis.com`.
2. Cloud Run service account gets `roles/aiplatform.user` (Terraform `workload_identity` module).
3. `SWITCHBOARD_GEMINI_PROVIDER=vertex`, `SWITCHBOARD_VERTEX_PROJECT=<project>`, `SWITCHBOARD_VERTEX_LOCATION=europe-west4`.

The `google-genai` client picks up Application Default Credentials. EU residency, Customer Data Use commitments, no training on inputs.

## Fortnox

OAuth 2.0 Authorization Code flow. Tokens: access 1h, refresh 45 days (Fortnox rotates both on each refresh — we store atomically).

1. https://developer.fortnox.se/ → Sign up → application type "Integrationspartner". Approval ~1–3 business days.
2. Create OAuth application → redirect URL `https://app.switchboard.se/api/integrations/fortnox/callback`.
3. Scopes: `companyinformation customer invoice bookkeeping settings`.
4. Set `SWITCHBOARD_FORTNOX_CLIENT_ID` + `SWITCHBOARD_FORTNOX_CLIENT_SECRET` in Secret Manager.
5. Owner clicks "Anslut Fortnox" in Settings → backend redirects to Fortnox consent → callback persists per-tenant tokens (KMS-encrypted via per-firma CryptoKey).
6. Trigger initial customer sync: `POST /api/integrations/fortnox/sync` (also runs on a 60s schedule once Cloud Tasks is wired).

Source: `backend/src/switchboard/integrations/fortnox.py`.

## Visma eEkonomi

Same shape as Fortnox. Identity provider: `https://identity.vismaonline.com/connect/authorize`. API base: `https://eaccountingapi.vismaonline.com/v2/`. Scope: `ea:api offline_access`.

1. https://developer.visma.com/ → Sign up.
2. Create application → redirect URL `https://app.switchboard.se/api/integrations/visma/callback`.
3. `SWITCHBOARD_VISMA_CLIENT_ID` + `SWITCHBOARD_VISMA_CLIENT_SECRET` in Secret Manager.

Source: `backend/src/switchboard/integrations/visma_eekonomi.py`.

## Google Calendar

Reuses the same Google OAuth client used by NextAuth, plus the
`https://www.googleapis.com/auth/calendar.events` scope.

1. GCP console → Credentials → OAuth client → Authorized redirect URIs include `https://app.switchboard.se/api/integrations/google-calendar/callback`.
2. `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_ID` + `SWITCHBOARD_GOOGLE_OAUTH_CLIENT_SECRET` in Secret Manager.

Bidirectional sync: AI bookings create events; existing busy slots are read on `check_availability` to avoid double-booking.

Source: `backend/src/switchboard/integrations/google_calendar.py`.

## Stripe Billing

Recommended flow per https://docs.stripe.com/billing/subscriptions/build-subscriptions.

1. Stripe Dashboard → create three Products + recurring monthly Prices: Starter (1495 SEK), Professional (2995 SEK), Premium (5995+ SEK).
2. Set the price ids in env: `SWITCHBOARD_STRIPE_PRICE_STARTER`, `_PROFESSIONAL`, `_PREMIUM`.
3. Webhook endpoint: `POST https://app.switchboard.se/api/billing/webhook` with events `checkout.session.completed`, `customer.subscription.{created,updated,deleted}`, `invoice.{paid,payment_failed}`. Copy the webhook signing secret to `SWITCHBOARD_STRIPE_WEBHOOK_SECRET`.
4. From the dashboard, owner clicks "Uppgradera plan" → backend creates a Checkout Session → owner pays → webhook flips `Firma.subscription_status` to `active` and updates `Firma.plan` from the price.
5. Plan limits enforced at call ingress (`integrations.stripe_billing.check_call_allowed`); over-quota or delinquent firmor get a busy-tone hangup.

Source: `backend/src/switchboard/integrations/stripe_billing.py`.

## Hantverksdata Next (partner-gated)

Long-running partneravtal:

1. Email `partners@hantverksdata.se` with a 1-page deck + concrete demo.
2. ETA 2–4 months. On approval, API credentials land in Secret Manager + per-tenant DEK-encrypted refresh tokens follow the same shape as Fortnox.

Strategic moat (PRD §8.7.2). The integration shape mirrors Fortnox (auth-code OAuth, customer + project endpoints) so swapping the client should be a 1-week task once credentials arrive.

## Bolagsverket

Public org-number lookup, no auth. Currently invoked inline; cache via Memorystore Redis in production once concurrent firmor justify it.

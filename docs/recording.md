# Recording pipeline

## Lifecycle

```
caller speech ── 46elks ── bridge ── (caller leg buffered)
                                              │
                                              ▼
              gemini ── (ai leg buffered) ── recording_buffer
                                              │
                                  call ends   │
                                              ▼
                                  mix to mono PCM 24kHz
                                              │
                              ffmpeg → MP3 (or WAV fallback)
                                              │
                                              ▼
                          per-tenant GCS bucket (CMEK)
                                              │
                              signed URL (1h) → Call.recording_url
```

## Per-tenant isolation (PRD §8.9)

- One bucket per firma: `switchboard-rec-{firma_id_lower}-europe-west4`
- Per-tenant CMEK: `projects/{p}/locations/europe-west4/keyRings/switchboard/cryptoKeys/firma-{id_lower}`
- `LocalStorage` (dev) refuses path traversal and tenant-cross-reads
- `GCSStorage` (prod) writes only to the firma's bucket; cross-firma reads return `NotFound`

## Eager bucket creation

The first call for a firma will fail mid-stream if the bucket doesn't exist. Onboarding (Step 12 of next-steps) calls `make_storage().ensure_bucket(firma_id)` synchronously — fails fast on KMS / IAM misconfiguration.

## Encoding

Production container has `ffmpeg` (see `Dockerfile.bridge`). MP3 64kbps mono, ~30 KB/min — small, plays everywhere.

If `ffmpeg` isn't on PATH (dev without it installed), the service writes WAV instead. The dashboard handles both transparently via the `<audio>` tag.

## Retention

Default 7 days (PRD §9.6). Implemented as a GCS Lifecycle rule on the bucket: `Delete after 7 days`. Per-firma retention extension (up to 365) edits the rule when settings change.

## Signed URL access

Dashboard never embeds raw `gs://` URIs. `Call.recording_url` is a v4 signed URL with 1h expiry. The owner reloads the call detail page if the URL expires; mobile app keeps a token-refresh on background.

## Tenant erasure

`GCSStorage.delete_tenant(firma_id)` runs `bucket.delete(force=True)`. Combined with destroying the per-tenant KMS key version, this is provably irrecoverable even from Google's backups.

## Limits

- Bridge holds the full call's audio in memory (typical 5MB for a 10-minute call). Cloud Run task memory limit is 2 Gi (set in Terraform). For longer calls (>1 hour), spill to a tmpfile — not needed for MVP.
- ffmpeg subprocess is synchronous and blocks the bridge for ~50–200 ms after call end. Acceptable; future move to a Cloud Tasks worker for offline encoding if it ever becomes a hot path.

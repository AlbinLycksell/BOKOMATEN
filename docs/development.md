# Development

## Prerequisites

- Python 3.13 (via `uv` — auto-fetched)
- `uv` ≥ 0.11
- Node 20+ and pnpm 10
- macOS dev: `brew install portaudio` (only required for `scripts/gem_live.py`, not the backend)

## First-time setup

```bash
git clone git@github.com:AlbinLycksell/BOKOMATEN.git auto-booker
cd auto-booker

# backend
cd backend
uv sync --extra dev

# web
cd ../web
pnpm install
```

Add a `GEMINI_API_KEY` to `.env.local` (gitignored). `.env` is the committed template.

## Running

Two terminals.

**Backend (single-deployable mode):**

```bash
cd backend
uv run uvicorn switchboard.app:create_app --factory --reload --port 8000
# OpenAPI:    http://127.0.0.1:8000/docs
# Health:     http://127.0.0.1:8000/health
# Inbox WS:   ws://127.0.0.1:8000/ws/inbox/<firma_id>
# Bridge WS:  ws://127.0.0.1:8000/ws/bridge/<firma_id>/<call_id>
# Tool RPC:   POST http://127.0.0.1:8000/api/tools/dispatch
```

The first run seeds Anderssons VVS AB with Inger, Karim, Pelle, three demo calls, and tool-invocation history (see `db/seed.py`).

**Backend (prod-shape, two services):**

```bash
# Application Backend
cd backend
uv run uvicorn switchboard.app:create_app --factory --port 8000

# Realtime Bridge — separate terminal, separate port
SWITCHBOARD_TOOL_DISPATCH_MODE=http \
SWITCHBOARD_APPLICATION_BACKEND_URL=http://127.0.0.1:8000 \
SWITCHBOARD_BRIDGE_INTERNAL_TOKEN=dev-token \
uv run uvicorn switchboard.bridge_app:create_bridge_app --factory --port 8001
```

This mirrors the production split where the two run as independent Cloud Run services with mTLS over a VPC connector.

**Web:**

```bash
cd web
pnpm dev   # http://localhost:3000
```

`/api/*` is proxied to the backend (see `next.config.ts`). The dashboard sends an `X-Firma-Id` header for the seeded demo firma until OAuth lands.

## Daily loop

| Task | Command |
|---|---|
| Add a Python dep | `cd backend && uv add <pkg>` |
| Add a JS dep | `cd web && pnpm add <pkg>` |
| Run backend tests | `cd backend && uv run pytest -q` |
| Lint / format Python | `uv run ruff check . && uv run ruff format .` |
| Type-check Python | `uv run pyright` |
| Type-check web | `cd web && pnpm typecheck` |
| Production web build | `cd web && pnpm build` |
| Regenerate OpenAPI types | `cd backend && uv run dump-openapi && cd ../web && pnpm gen:api` |

## Conventions

- Branches: `<issue#>-<slug>` for issue-tracked work, `fix-<slug>` for tiny intermediates.
- Commits: Conventional — `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`.
- One commit per logical unit, not per file. Don't bundle unrelated changes.
- Never commit to `main` or `release-*` directly.
- Pre-PR review: walk every changed file in your own diff and ask "is anything off?" before opening the PR.

## Where things live

| Want to | Path |
|---|---|
| Add a tool the AI can call | `backend/src/switchboard/tools/` (see `docs/tools.md`) |
| Change emergency rules | `backend/src/switchboard/services/triage_service.py` |
| Change the AI's system prompt | `backend/src/switchboard/bridge/system_prompt.py` |
| Add an API route | `backend/src/switchboard/api/routes_<area>.py` |
| Add a dashboard view | `web/app/(app)/<route>/page.tsx` (see `docs/frontend.md`) |
| Tweak the design language | `web/styles/tokens.css` (see `docs/frontend.md`) |
| Update the data model | `backend/src/switchboard/models/` (see `docs/data-model.md`) |
| Read the PRD | [`../PRD.md`](../PRD.md) |
| Read the implementation plan | [`./superpowers/plans/2026-05-09-switchboard-mvp-foundation.md`](./superpowers/plans/2026-05-09-switchboard-mvp-foundation.md) |

## Troubleshooting

- **`uv sync` fails on Python 3.13:** uv will auto-download. Verify `.python-version` reads `3.13` and rerun.
- **`pnpm dev` shows old types:** rerun `pnpm gen:api` after backend schema changes.
- **`/inbox` shows the empty state:** backend isn't reachable on `:8000`, or the seeded firma id doesn't match. Check `X-Firma-Id` in `web/lib/api.ts`.
- **Audio tests slow on first run:** scipy's resample_poly does a one-time JIT-ish import. Subsequent runs are fast.
- **Pyaudio install fails on macOS:** `brew install portaudio` (only needed for `scripts/gem_live.py`).

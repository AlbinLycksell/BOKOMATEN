# Switchboard Web

Owner dashboard. Next.js 15 / React 19 / TypeScript / Tailwind v4. Nordic minimal — hairlines and tone, no shadows.

```bash
cd web
pnpm install
pnpm dev   # http://localhost:3000
```

Backend OpenAPI types are generated into `lib/api-types.ts`:

```bash
# from backend/
uv run dump-openapi
# from web/
pnpm gen:api
```

Design system reference: [`docs/frontend.md`](../docs/frontend.md).

# Svarsa Backend

Python 3.13 / FastAPI / Pydantic v2 / SQLModel.

```bash
cd backend
uv sync
uv run uvicorn svarsa.app:create_app --factory --reload --port 8000
```

See [`docs/backend.md`](../docs/backend.md) for module layout and conventions, and [`docs/development.md`](../docs/development.md) for the full dev loop.

.PHONY: help install hooks test typecheck build dev backend web openapi secrets-scan clean

help:
	@echo "Switchboard — common dev commands"
	@echo ""
	@echo "  make install        Install backend + web dependencies"
	@echo "  make hooks          Install pre-commit hooks (run once per clone)"
	@echo "  make test           Run backend tests"
	@echo "  make typecheck      Run web typecheck"
	@echo "  make build          Run web production build"
	@echo "  make dev            Start backend (8000) and web (3000) in parallel"
	@echo "  make backend        Start backend only"
	@echo "  make web            Start web only"
	@echo "  make openapi        Dump backend OpenAPI and regen web types"
	@echo "  make secrets-scan   Run gitleaks against the full git history"
	@echo "  make clean          Remove build artifacts and caches"

install:
	cd backend && uv sync --extra dev
	cd web && pnpm install

test:
	cd backend && uv run pytest -q

typecheck:
	cd web && pnpm typecheck

build:
	cd web && pnpm build

backend:
	cd backend && uv run uvicorn switchboard.app:create_app --factory --reload --port 8000

web:
	cd web && pnpm dev

dev:
	@echo "Starting backend on :8000 and web on :3000…"
	@(cd backend && uv run uvicorn switchboard.app:create_app --factory --reload --port 8000) & \
	 (cd web && pnpm dev) & \
	 wait

openapi:
	cd backend && uv run dump-openapi
	cd web && pnpm gen:api

hooks:
	@command -v pre-commit >/dev/null 2>&1 || { \
		echo "pre-commit not installed. Install with: pipx install pre-commit  (or: pip install --user pre-commit)"; \
		exit 1; \
	}
	pre-commit install
	@echo "Pre-commit hooks installed. Run \`pre-commit run --all-files\` to scan everything."

secrets-scan:
	@command -v gitleaks >/dev/null 2>&1 || { \
		echo "gitleaks not installed. Install with: brew install gitleaks  (macOS)"; \
		echo "                              or: go install github.com/gitleaks/gitleaks/v8@latest"; \
		exit 1; \
	}
	gitleaks detect --source . --config .gitleaks.toml --redact --verbose --no-banner

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/openapi.json backend/switchboard.db backend/switchboard.db-journal
	rm -rf web/.next web/.turbo web/lib/openapi.json

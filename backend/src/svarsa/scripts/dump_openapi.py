"""Dump the FastAPI OpenAPI spec to disk for downstream codegen."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from svarsa.app import create_app

DEFAULT_OUT = Path(__file__).resolve().parents[3] / "openapi.json"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    out_path = Path(args[0]) if args else DEFAULT_OUT
    app = create_app()
    spec = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Dev seed data — extended in Phase 2 once models exist."""

from __future__ import annotations

from svarsa.core.logging import get_logger

log = get_logger("svarsa.seed")


def seed_dev_data() -> None:
    log.info("seed.skipped", reason="phase-2-extends-this")

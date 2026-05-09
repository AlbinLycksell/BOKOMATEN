from __future__ import annotations

import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)
from structlog.stdlib import BoundLogger

from switchboard.core.config import Settings


def configure_logging(settings: Settings) -> None:
    timestamper = TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        merge_contextvars,
        add_log_level,
        timestamper,
        StackInfoRenderer(),
        format_exc_info,
    ]
    renderer = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=settings.log_level,
        handlers=[logging.StreamHandler(sys.stderr)],
        format="%(message)s",
    )


def get_logger(name: str | None = None) -> BoundLogger:
    return structlog.get_logger(name)

"""
Structured logging configuration using ``structlog``.

This module configures a project-wide structured logger that outputs
JSON-formatted log events in production and human-readable coloured output
during development.  Every module should obtain its logger via::

    from derim.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys

import structlog

from derim.config import get_settings


def configure_logging() -> None:
    """
    Configure ``structlog`` and the standard-library ``logging`` module.

    Call this function once at application startup (e.g. in ``main.py``).
    The log level and output format are driven by the application settings.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Shared processors applied to every log event.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.app_env == "production":
        # Machine-readable JSON in production.
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Coloured, human-readable output for development.
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers.
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a bound ``structlog`` logger for the given module *name*.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module.

    Returns
    -------
    structlog.stdlib.BoundLogger
        A structured logger instance.
    """
    return structlog.get_logger(name)

"""Application logging configuration."""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    """Configure the process-wide logging level and format."""
    numeric_level = getattr(logging, level)
    logging.basicConfig(level=numeric_level, format=_LOG_FORMAT)
    logging.getLogger().setLevel(numeric_level)

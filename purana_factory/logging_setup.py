"""Loguru logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from purana_factory.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    log_path = settings.resolve_path(settings.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.logging.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )
    logger.add(
        str(log_path),
        level=settings.logging.level,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        encoding="utf-8",
    )

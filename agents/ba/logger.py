"""Logging configuration for BA AI Agent."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def setup_logger(
    agent_id: str = "ba-01",
    log_dir: str | Path | None = None,
    log_filename: str = "agent_ba.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configures structured logging to stdout and rotating/standard file."""
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / log_filename

    logger = logging.getLogger(f"agent.{agent_id}")
    logger.setLevel(level)

    # Avoid duplicate handlers on re-init
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger

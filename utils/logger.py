"""
HireLens AI — Structured Logging
Provides a consistent logger used across all modules.
"""

from __future__ import annotations
import logging
import sys
from functools import lru_cache


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@lru_cache(maxsize=None)
def get_logger(name: str = "hirelens") -> logging.Logger:
    """
    Return a module-level logger. Cached so the same instance is
    returned for the same name across the entire process.

    Usage:
        from utils.logger import get_logger
        log = get_logger(__name__)
        log.info("Analysis started")
    """
    # Lazy import to avoid circular dependency with config
    try:
        from config import get_app_config
        cfg = get_app_config()
        level_str = cfg.log_level
        log_to_file = cfg.log_to_file
        log_file_path = cfg.log_file_path
    except Exception:
        level_str = "INFO"
        log_to_file = False
        log_file_path = "hirelens.log"

    level = getattr(logging, level_str.upper(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger  # Already configured

    formatter = _build_formatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_to_file:
        try:
            file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning(f"Could not open log file {log_file_path}: {e}")

    logger.propagate = False
    return logger


class AgentLogger:
    """
    Thin wrapper for per-agent structured log events.
    Prints consistent [AGENT][stage] messages for the analysis pipeline.
    """

    def __init__(self, agent_name: str):
        self._log = get_logger(f"hirelens.agent.{agent_name.lower().replace(' ', '_')}")
        self.agent_name = agent_name

    def start(self, resume_chars: int, jd_chars: int):
        self._log.info(
            f"[{self.agent_name}] Starting | resume={resume_chars}c jd={jd_chars}c"
        )

    def done(self, score_key: str = "", score: int = -1):
        extra = f" | {score_key}={score}" if score >= 0 else ""
        self._log.info(f"[{self.agent_name}] Complete{extra}")

    def parse_error(self, raw_preview: str):
        self._log.warning(
            f"[{self.agent_name}] JSON parse error | raw_preview={raw_preview[:120]!r}"
        )

    def error(self, msg: str, exc: Exception | None = None):
        self._log.error(f"[{self.agent_name}] {msg}", exc_info=exc)

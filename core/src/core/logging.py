"""Shared logging setup: a compact coloured formatter with per-level emoji.

Ported from ``manga_manager/packer``. Every flacifly CLI calls :func:`setup_logging`
and exposes ``--verbose`` / ``--loglevel``.
"""

from __future__ import annotations

import logging
from typing import Optional


class ColorFormatter(logging.Formatter):
    """Format records as ``<emoji> LEVEL: message`` with optional ANSI colour."""

    COLORS = {
        "DEBUG": "\x1b[34m",  # blue
        "INFO": "\x1b[32m",  # green
        "WARNING": "\x1b[33m",  # yellow
        "ERROR": "\x1b[31m",  # red
        "CRITICAL": "\x1b[31;1m",
    }
    EMOJI = {
        "DEBUG": "🔧",
        "INFO": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "💥",
    }
    RESET = "\x1b[0m"

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        emoji = self.EMOJI.get(level, "")
        if self.use_color:
            color = self.COLORS.get(level, "")
            prefix = f"{color}{emoji} {level}:{self.RESET}"
        else:
            prefix = f"{emoji} {level}:"
        msg = record.getMessage()
        formatted = f"{prefix} {msg}"
        if record.exc_info:
            formatted = f"{formatted}\n{self.formatException(record.exc_info)}"
        return formatted


def _resolve_level(verbose: bool, loglevel: Optional[str]) -> int:
    """Return a numeric logging level (``loglevel`` overrides ``verbose``)."""
    if loglevel:
        lvl = loglevel.upper()
        if lvl == "WARN":
            lvl = "WARNING"
        return getattr(logging, lvl, logging.INFO)
    return logging.DEBUG if verbose else logging.INFO


def setup_logging(
    verbose: bool = False,
    loglevel: Optional[str] = None,
    force_color: Optional[bool] = None,
) -> None:
    """Configure the root logger with the coloured formatter and emoji.

    - ``verbose`` -> DEBUG level, otherwise INFO.
    - ``loglevel``: explicit string level to override verbose
      (e.g. ``DEBUG|INFO|WARNING|ERROR|CRITICAL|WARN``).
    - ``force_color``: True/False to override automatic TTY detection.
    """
    root = logging.getLogger()
    root.handlers.clear()

    level = _resolve_level(verbose, loglevel)
    handler = logging.StreamHandler()

    stream = handler.stream
    if force_color is True:
        use_color = True
    elif force_color is False:
        use_color = False
    else:
        use_color = hasattr(stream, "isatty") and stream.isatty()

    handler.setFormatter(ColorFormatter(use_color))
    root.setLevel(level)
    root.addHandler(handler)

"""Tests for core.logging: level resolution and the coloured formatter."""

from __future__ import annotations

import logging

from core.logging import ColorFormatter, _resolve_level, setup_logging


def _record(level: int, msg: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_resolve_level_verbose():
    assert _resolve_level(True, None) == logging.DEBUG
    assert _resolve_level(False, None) == logging.INFO


def test_resolve_level_explicit_overrides_verbose():
    assert _resolve_level(True, "ERROR") == logging.ERROR
    assert _resolve_level(False, "debug") == logging.DEBUG


def test_resolve_level_warn_alias():
    assert _resolve_level(False, "WARN") == logging.WARNING


def test_resolve_level_unknown_falls_back_to_info():
    assert _resolve_level(False, "NOPE") == logging.INFO


def test_formatter_plain_has_emoji_and_no_ansi():
    out = ColorFormatter(use_color=False).format(_record(logging.INFO, "hi"))
    assert "INFO:" in out and "hi" in out
    assert "\x1b[" not in out
    assert "✅" in out


def test_formatter_color_wraps_ansi():
    out = ColorFormatter(use_color=True).format(_record(logging.ERROR, "boom"))
    assert out.startswith(ColorFormatter.COLORS["ERROR"])
    assert ColorFormatter.RESET in out
    assert "boom" in out


def test_setup_logging_sets_level_and_single_handler():
    setup_logging(verbose=True, force_color=False)
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    # Idempotent: calling again clears the previous handler.
    setup_logging(verbose=False, force_color=False)
    assert root.level == logging.INFO
    assert len(root.handlers) == 1

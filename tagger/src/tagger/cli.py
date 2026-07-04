"""CLI for ``flacifly-tag``: subcommands tag / dump / review / clear."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from core.logging import setup_logging

from .config import TagConfig
from .exit_codes import CLI_ERROR, SUCCESS
from .tagging import dump_directory, tag_directory

logger = logging.getLogger("tagger")


class _CLIError(Exception):
    """Raised after logging a CLI-level error so main() can return CLI_ERROR."""


def _add_logging_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--verbose", action="store_true", help="verbose logging")
    p.add_argument(
        "--loglevel",
        "-l",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "WARN"],
        help="explicit log level (overrides --verbose)",
    )


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("path", type=Path, help="FLAC file or directory to process")
    p.add_argument("--db", type=Path, default=None, help="SQLite DB path override")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Identify and tag FLAC files")
    sub = parser.add_subparsers(dest="command", help="command to execute")

    tag_p = sub.add_parser("tag", help="identify and tag; queue uncertain for review")
    _add_common_args(tag_p)
    tag_p.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="min confidence to auto-tag; below goes to the review queue (default 0.8)",
    )
    tag_p.add_argument("--dry-run", action="store_true", help="simulate; write nothing")
    _add_logging_args(tag_p)

    dump_p = sub.add_parser("dump", help="print current tags for FLAC files")
    _add_common_args(dump_p)
    _add_logging_args(dump_p)

    return parser


def _build_config(args: argparse.Namespace) -> TagConfig:
    kwargs: dict = {
        "path": args.path,
        "confidence_threshold": getattr(args, "confidence_threshold", 0.8),
        "dry_run": getattr(args, "dry_run", False),
        "verbose": args.verbose,
        "loglevel": args.loglevel,
    }
    if getattr(args, "db", None) is not None:
        kwargs["db_path"] = args.db
    cfg = TagConfig(**kwargs)
    if not cfg.path.exists():
        logger.error("path does not exist: %s", cfg.path)
        raise _CLIError
    return cfg


def main(argv=None) -> int:
    """Command-line entry point for ``flacifly-tag``."""
    args = _build_parser().parse_args(argv)

    if not args.command:
        _build_parser().print_help()
        return CLI_ERROR

    setup_logging(args.verbose, loglevel=args.loglevel)

    try:
        cfg = _build_config(args)
    except _CLIError:
        return CLI_ERROR

    if args.command == "tag":
        tag_directory(cfg)
        return SUCCESS
    if args.command == "dump":
        dump_directory(cfg)
        return SUCCESS

    return CLI_ERROR

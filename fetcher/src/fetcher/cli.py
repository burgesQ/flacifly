"""CLI for ``flacifly-fetch``: argument parsing, config building, orchestration."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from core.locking import LockError, job_lock
from core.logging import setup_logging

from .config import MODE_OFF, MODES, FetchConfig
from .downloader import run
from .exit_codes import CLI_ERROR, LOCKED
from .types_ import FetchTarget  # noqa: F401  (re-exported for convenience)

logger = logging.getLogger(__name__)


class _CLIError(Exception):
    """Raised after logging a CLI-level error so main() can return CLI_ERROR."""


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Download best-quality audio and keep it for FLAC transcoding."
    )
    p.add_argument(
        "--download-root",
        type=Path,
        required=True,
        help="root directory to download into (per-target subdirs are created)",
    )
    p.add_argument("--targets", type=Path, default=None, help="path to targets.conf")
    p.add_argument(
        "--url", type=str, default=None, help="single URL to fetch (one-off)"
    )
    p.add_argument("--ytdlp-conf", type=Path, default=None, help="yt-dlp option file")
    p.add_argument("--cookies", type=Path, default=None, help="cookies.txt for auth")
    p.add_argument(
        "--mode",
        choices=MODES,
        default=MODE_OFF,
        help="which sources to process (off = safe no-op default)",
    )
    p.add_argument(
        "--no-keep-original",
        action="store_true",
        help="delete the lossy source after transcoding to FLAC",
    )
    p.add_argument(
        "--flac-compression",
        type=int,
        default=8,
        help="FLAC compression level 0..12 (default 8)",
    )
    p.add_argument(
        "--nb-worker",
        type=int,
        default=1,
        help="number of parallel workers (default 1)",
    )
    p.add_argument("--db", type=Path, default=None, help="SQLite DB path override")
    p.add_argument("--dry-run", action="store_true", help="simulate; download nothing")
    p.add_argument("--verbose", action="store_true", help="verbose logging")
    p.add_argument(
        "--loglevel",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "WARN"],
        help="explicit log level (overrides --verbose)",
    )
    return p


def _build_config(args: argparse.Namespace) -> FetchConfig:
    """Build a FetchConfig from parsed args. Raises _CLIError on invalid input."""
    if args.url is None and args.targets is None and args.mode != MODE_OFF:
        logger.error("either --url or --targets must be provided (unless --mode off)")
        raise _CLIError

    kwargs: dict = {
        "download_root": args.download_root,
        "targets_file": args.targets,
        "ytdlp_conf": args.ytdlp_conf,
        "cookies": args.cookies,
        "mode": args.mode,
        "url": args.url,
        "keep_original": not args.no_keep_original,
        "flac_compression": args.flac_compression,
        "nb_worker": args.nb_worker,
        "dry_run": args.dry_run,
        "verbose": args.verbose,
        "loglevel": args.loglevel,
    }
    if args.db is not None:
        kwargs["db_path"] = args.db
    return FetchConfig(**kwargs)


def main(argv=None) -> int:
    """Command-line entry point for ``flacifly-fetch``."""
    args = _build_parser().parse_args(argv)
    setup_logging(args.verbose, loglevel=args.loglevel)

    try:
        cfg = _build_config(args)
    except _CLIError:
        return CLI_ERROR

    now = datetime.now(timezone.utc).isoformat()
    try:
        with job_lock(cfg.lock_dir, "fetch"):
            return run(cfg, now=now)
    except LockError as e:
        logger.error(str(e))
        return LOCKED

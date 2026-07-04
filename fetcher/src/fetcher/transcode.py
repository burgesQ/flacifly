"""Transcode a downloaded best-audio file to FLAC via FFmpeg.

The lossy source is a lossless *container* target only — FLAC-from-lossy recovers no
fidelity, but is produced for CDJ/rekordbox compatibility (see README). The original is
kept unless the caller opts out. The subprocess runner is injectable for testing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# A runner takes an argv list and returns the process return code.
Runner = Callable[[List[str]], int]


def _default_runner(cmd: List[str]) -> int:
    import subprocess

    return subprocess.run(cmd, capture_output=True).returncode


def flac_path_for(original: Path) -> Path:
    """Return the sibling ``.flac`` path for a source file."""
    return original.with_suffix(".flac")


def needs_transcode(original: Path, flac: Path) -> bool:
    """True if the FLAC is missing or older than its source (idempotency guard)."""
    if not flac.exists():
        return True
    return flac.stat().st_mtime < original.stat().st_mtime


def build_ffmpeg_cmd(original: Path, flac: Path, compression: int) -> List[str]:
    """Build the FFmpeg argv for a lossless FLAC re-encode carrying metadata."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(original),
        "-c:a",
        "flac",
        "-compression_level",
        str(compression),
        "-map_metadata",
        "0",
        str(flac),
    ]


def transcode_to_flac(
    original: Path,
    *,
    compression: int = 8,
    runner: Runner = _default_runner,
    dry_run: bool = False,
) -> Optional[Path]:
    """Transcode ``original`` to a sibling FLAC. Idempotent; returns the FLAC path.

    Returns None if FFmpeg fails. On dry-run, logs intent and returns the target path
    without touching the filesystem.
    """
    flac = flac_path_for(original)
    if not needs_transcode(original, flac):
        logger.debug("FLAC up to date, skipping: %s", flac)
        return flac

    cmd = build_ffmpeg_cmd(original, flac, compression)
    if dry_run:
        logger.info("[DRY RUN] would transcode: %s → %s", original.name, flac.name)
        return flac

    rc = runner(cmd)
    if rc != 0:
        logger.error("ffmpeg failed (rc=%d) for %s", rc, original)
        return None
    logger.debug("transcoded → %s", flac)
    return flac

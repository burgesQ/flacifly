"""Shared structured types and constants for flacifly.

Row NamedTuples for the SQLite layer live here (used by ``core.db``).
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Optional, TypeAlias

# A path accepted from the CLI or config (string) or already a Path.
PathLike: TypeAlias = str | Path


class TrackStatus:
    """String status values for ``tracks.status`` (no bare literals in code)."""

    DOWNLOADED = "downloaded"
    TRANSCODED = "transcoded"
    TAGGED = "tagged"
    FAILED = "failed"


class ReviewDecision:
    """String decision values for ``review_queue.decision``."""

    ACCEPTED = "accepted"
    EDITED = "edited"
    SKIPPED = "skipped"


class TrackRow(NamedTuple):
    """A row of the ``tracks`` table. ``id`` is None before insertion."""

    source: str
    source_id: str
    target_dir: str
    downloaded_at: str
    status: str = TrackStatus.DOWNLOADED
    source_url: Optional[str] = None
    raw_title: Optional[str] = None
    original_path: Optional[str] = None
    flac_path: Optional[str] = None
    embedded_json: Optional[str] = None
    id: Optional[int] = None


class ReviewRow(NamedTuple):
    """A row of the ``review_queue`` table. ``id`` is None before insertion."""

    track_id: int
    confidence: float
    guessed_artist: Optional[str] = None
    guessed_title: Optional[str] = None
    guessed_date: Optional[str] = None
    resolved: bool = False
    decision: Optional[str] = None
    id: Optional[int] = None

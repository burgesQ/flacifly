"""Shared fixtures for core tests (factory pattern)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core import db
from core.types_ import TrackRow


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """An initialised, empty flacifly DB in a temp dir."""
    path = tmp_path / "flacifly.db"
    db.init_db(path)
    return path


@pytest.fixture
def make_track():
    """Factory building a TrackRow with sensible defaults."""

    def _make_track(
        *,
        source: str = "youtube",
        source_id: str = "abc123",
        target_dir: str = "YouTube",
        raw_title: str = "Artist - Title",
        downloaded_at: str = "2026-07-04T00:00:00Z",
        **kwargs,
    ) -> TrackRow:
        return TrackRow(
            source=source,
            source_id=source_id,
            target_dir=target_dir,
            raw_title=raw_title,
            downloaded_at=downloaded_at,
            **kwargs,
        )

    return _make_track

"""Shared fixtures for tagger tests (factory pattern)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "silence.flac"


@pytest.fixture
def make_flac(tmp_path: Path):
    """Factory copying the bundled silent FLAC to a fresh, writable path."""

    def _make_flac(name: str = "song.flac", *, subdir: str = ".") -> Path:
        dest = tmp_path / subdir / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_FIXTURE, dest)
        return dest

    return _make_flac

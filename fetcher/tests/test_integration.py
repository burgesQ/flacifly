"""Integration smoke tests (opt-in).

- The FFmpeg test runs whenever ffmpeg is on PATH (deterministic, no network).
- The live-download test only runs when FLACIFLY_INTEGRATION=1 is set, since it hits
  the network and depends on a public URL staying up.

Run just these with: ``uv run pytest -m integration``.
"""

from __future__ import annotations

import os
import shutil
import wave
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fetcher.transcode import transcode_to_flac

pytestmark = pytest.mark.integration

_HAS_FFMPEG = shutil.which("ffmpeg") is not None
_LIVE = os.environ.get("FLACIFLY_INTEGRATION") == "1"


def _make_wav(path: Path) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 800)  # ~0.1s of silence
    return path


@pytest.mark.skipif(not _HAS_FFMPEG, reason="ffmpeg not installed")
def test_real_ffmpeg_transcode_to_flac(tmp_path: Path):
    src = _make_wav(tmp_path / "clip.wav")
    flac = transcode_to_flac(src, compression=0)  # real ffmpeg runner
    assert flac is not None and flac.exists()
    assert flac.suffix == ".flac"
    assert flac.stat().st_size > 0
    assert src.exists()  # original kept


@pytest.mark.skipif(not (_LIVE and _HAS_FFMPEG), reason="set FLACIFLY_INTEGRATION=1")
def test_live_fetch_youtube(tmp_path: Path):
    from fetcher.config import MODE_YOUTUBE, FetchConfig
    from fetcher.downloader import run
    from fetcher.exit_codes import SUCCESS

    # A short Creative Commons clip; override via FLACIFLY_TEST_URL if it disappears.
    url = os.environ.get(
        "FLACIFLY_TEST_URL", "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    )
    cfg = FetchConfig(
        download_root=tmp_path / "dl",
        db_path=tmp_path / "db.sqlite",
        lock_dir=tmp_path / "locks",
        mode=MODE_YOUTUBE,
        url=url,
    )
    rc = run(cfg, now=datetime.now(timezone.utc).isoformat())
    assert rc == SUCCESS
    flacs = list((tmp_path / "dl").rglob("*.flac"))
    assert flacs, "expected at least one FLAC produced"

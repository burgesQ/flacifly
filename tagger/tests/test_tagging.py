"""Tests for tagger.tagging: confident auto-tag vs review-queue, dry-run."""

from __future__ import annotations

import json
from pathlib import Path

from core import db
from core.types_ import TrackRow
from tagger.config import TagConfig
from tagger.tagging import tag_directory
from tagger.tags import read_tags


def _cfg(tmp_path: Path, music: Path, **kw) -> TagConfig:
    defaults = dict(path=music, db_path=tmp_path / "db.sqlite", lock_dir=tmp_path / "l")
    defaults.update(kw)
    return TagConfig(**defaults)  # type: ignore[arg-type]


def _add_track_for(
    cfg: TagConfig, flac: Path, *, source_id: str, embedded: dict, raw: str
):
    db.init_db(cfg.db_path)
    with db.connect(cfg.db_path) as conn:
        return db.add_track(
            conn,
            TrackRow(
                source="youtube",
                source_id=source_id,
                target_dir="d",
                raw_title=raw,
                flac_path=str(flac.resolve()),
                embedded_json=json.dumps(embedded),
                downloaded_at="2026-01-01T00:00:00Z",
            ),
        )


def test_confident_embedded_gets_tagged(make_flac, tmp_path):
    flac = make_flac("track.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    tid = _add_track_for(
        cfg, flac, source_id="1", embedded={"artist": "A", "track": "B"}, raw="whatever"
    )

    summary = tag_directory(cfg)
    assert summary.tagged == 1 and summary.queued == 0
    assert read_tags(flac)["ARTIST"] == "A"
    with db.connect(cfg.db_path) as conn:
        assert db.get_track(conn, tid).status == "tagged"


def test_uncertain_goes_to_review_queue(make_flac, tmp_path):
    flac = make_flac("track.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    tid = _add_track_for(
        cfg, flac, source_id="2", embedded={}, raw="no separator title"
    )

    summary = tag_directory(cfg)
    assert summary.tagged == 0 and summary.queued == 1
    assert read_tags(flac) == {}  # not tagged
    with db.connect(cfg.db_path) as conn:
        pending = db.pending_reviews(conn)
    assert len(pending) == 1 and pending[0].track_id == tid


def test_dry_run_writes_nothing_and_queues_nothing(make_flac, tmp_path):
    flac = make_flac("track.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music", dry_run=True)
    _add_track_for(
        cfg, flac, source_id="3", embedded={"artist": "A", "track": "B"}, raw="x"
    )

    tag_directory(cfg)
    assert read_tags(flac) == {}
    with db.connect(cfg.db_path) as conn:
        assert db.pending_reviews(conn) == []
        assert db.get_track(conn, 1).status == "downloaded"


def test_confident_heuristic_without_db_row(make_flac, tmp_path):
    # Filename encodes "Artist - Title"; no DB row exists.
    flac = make_flac("Artist - Title.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    db.init_db(cfg.db_path)

    summary = tag_directory(cfg)
    # Heuristic clean split = 0.75 < 0.8 default threshold → not auto-tagged, and no DB
    # row means it cannot be queued → skipped.
    assert summary.skipped == 1
    assert read_tags(flac) == {}


def test_heuristic_tagged_with_lower_threshold(make_flac, tmp_path):
    flac = make_flac("Artist - Title.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music", confidence_threshold=0.7)
    db.init_db(cfg.db_path)

    summary = tag_directory(cfg)
    assert summary.tagged == 1
    tags = read_tags(flac)
    assert tags["ARTIST"] == "Artist" and tags["TITLE"] == "Title"

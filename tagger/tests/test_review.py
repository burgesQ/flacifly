"""Tests for tagger.review: interactive accept / edit / skip / quit flow."""

from __future__ import annotations

from pathlib import Path

from core import db
from core.types_ import ReviewRow, TrackRow
from tagger.config import TagConfig
from tagger.review import review_pending
from tagger.tags import read_tags


def _cfg(tmp_path: Path, music: Path, **kw) -> TagConfig:
    defaults = dict(path=music, db_path=tmp_path / "db.sqlite", lock_dir=tmp_path / "l")
    defaults.update(kw)
    return TagConfig(**defaults)  # type: ignore[arg-type]


def _queue(cfg: TagConfig, flac: Path, *, artist=None, title=None, conf=0.3) -> int:
    db.init_db(cfg.db_path)
    with db.connect(cfg.db_path) as conn:
        tid = db.add_track(
            conn,
            TrackRow(
                source="youtube",
                source_id=flac.stem,
                target_dir="d",
                raw_title=flac.stem,
                flac_path=str(flac.resolve()),
                downloaded_at="2026-01-01T00:00:00Z",
            ),
        )
        db.enqueue_review(
            conn,
            ReviewRow(
                track_id=tid,
                confidence=conf,
                guessed_artist=artist,
                guessed_title=title,
            ),
        )
    return tid


def _scripted(answers):
    it = iter(answers)
    return lambda _prompt: next(it)


def test_review_accept_writes_guess(make_flac, tmp_path):
    flac = make_flac("t1.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    tid = _queue(cfg, flac, artist="Guessed", title="Song")

    out: list = []
    review_pending(cfg, prompt=_scripted([""]), out=out.append)

    assert read_tags(flac)["ARTIST"] == "Guessed"
    with db.connect(cfg.db_path) as conn:
        assert db.pending_reviews(conn) == []
        assert db.get_track(conn, tid).status == "tagged"


def test_review_edit_overrides_guess(make_flac, tmp_path):
    flac = make_flac("t2.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    _queue(cfg, flac, artist="Wrong", title="Wrong")

    review_pending(
        cfg, prompt=_scripted(["Real Artist - Real Title"]), out=lambda _s: None
    )

    tags = read_tags(flac)
    assert tags["ARTIST"] == "Real Artist" and tags["TITLE"] == "Real Title"


def test_review_skip_leaves_untagged_but_resolved(make_flac, tmp_path):
    flac = make_flac("t3.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    _queue(cfg, flac, artist="X", title="Y")

    review_pending(cfg, prompt=_scripted(["s"]), out=lambda _s: None)

    assert read_tags(flac) == {}
    with db.connect(cfg.db_path) as conn:
        assert db.pending_reviews(conn) == []  # resolved (skipped)


def test_review_quit_stops_and_keeps_remaining(make_flac, tmp_path):
    f1 = make_flac("a.flac", subdir="music")
    f2 = make_flac("b.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music")
    _queue(cfg, f1, artist="A1", title="T1")
    _queue(cfg, f2, artist="A2", title="T2")

    review_pending(cfg, prompt=_scripted(["q"]), out=lambda _s: None)

    with db.connect(cfg.db_path) as conn:
        # Nothing resolved — both still pending.
        assert len(db.pending_reviews(conn)) == 2


def test_review_nothing_pending(tmp_path):
    cfg = _cfg(tmp_path, tmp_path)
    db.init_db(cfg.db_path)
    out: list = []
    review_pending(cfg, prompt=_scripted([]), out=out.append)
    assert any("Nothing to review" in line for line in out)


def test_review_dry_run_persists_nothing(make_flac, tmp_path):
    flac = make_flac("t4.flac", subdir="music")
    cfg = _cfg(tmp_path, tmp_path / "music", dry_run=True)
    _queue(cfg, flac, artist="G", title="S")

    review_pending(cfg, prompt=_scripted([""]), out=lambda _s: None)

    assert read_tags(flac) == {}
    with db.connect(cfg.db_path) as conn:
        assert len(db.pending_reviews(conn)) == 1  # not resolved

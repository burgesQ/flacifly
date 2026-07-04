"""Tests for core.db: init idempotency, dedup, and review-queue round-trip."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core import db
from core.types_ import ReviewDecision, ReviewRow, TrackStatus


def test_init_db_is_idempotent(tmp_path: Path):
    path = tmp_path / "x.db"
    db.init_db(path)
    db.init_db(path)  # second call must not raise
    with db.connect(path) as conn:
        versions = conn.execute("SELECT version FROM schema_migrations").fetchall()
    assert [v["version"] for v in versions] == [db.SCHEMA_VERSION]


def test_init_db_creates_parent_dir(tmp_path: Path):
    path = tmp_path / "nested" / "dir" / "flacifly.db"
    db.init_db(path)
    assert path.exists()


def test_add_track_and_exists(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        assert not db.track_exists(conn, "youtube", "abc123")
        tid = db.add_track(conn, make_track())
        assert tid > 0
        assert db.track_exists(conn, "youtube", "abc123")

    # Persisted across connections (WAL / committed).
    with db.connect(db_path) as conn:
        row = db.get_track(conn, tid)
    assert row is not None
    assert row.source_id == "abc123"
    assert row.status == TrackStatus.DOWNLOADED


def test_add_track_duplicate_raises(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        db.add_track(conn, make_track())
        with pytest.raises(sqlite3.IntegrityError):
            db.add_track(conn, make_track())


def test_dedup_distinguishes_source(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        db.add_track(conn, make_track(source="youtube", source_id="dup"))
        # Same id but different source is a distinct track.
        db.add_track(conn, make_track(source="soundcloud", source_id="dup"))
        assert db.track_exists(conn, "youtube", "dup")
        assert db.track_exists(conn, "soundcloud", "dup")


def test_set_status_and_flac_path(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        tid = db.add_track(conn, make_track())
        db.set_status(conn, tid, TrackStatus.TAGGED)
        db.set_flac_path(conn, tid, "/music/x.flac")
        row = db.get_track(conn, tid)
    assert row is not None
    assert row.status == TrackStatus.TAGGED
    assert row.flac_path == "/music/x.flac"


def test_review_round_trip(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        tid = db.add_track(conn, make_track())
        rid = db.enqueue_review(
            conn,
            ReviewRow(
                track_id=tid,
                confidence=0.4,
                guessed_artist="Artist",
                guessed_title="Title",
            ),
        )
        assert rid > 0
        pending = db.pending_reviews(conn)
        assert len(pending) == 1 and pending[0].track_id == tid

        db.resolve_review(
            conn, rid, ReviewDecision.EDITED, guessed_artist="Real Artist"
        )
        assert db.pending_reviews(conn) == []
        stored = conn.execute(
            "SELECT guessed_artist, decision, resolved FROM review_queue WHERE id = ?",
            (rid,),
        ).fetchone()
    assert stored["guessed_artist"] == "Real Artist"
    assert stored["decision"] == ReviewDecision.EDITED
    assert stored["resolved"] == 1


def test_enqueue_review_upserts_on_conflict(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        tid = db.add_track(conn, make_track())
        r1 = db.enqueue_review(conn, ReviewRow(track_id=tid, confidence=0.3))
        r2 = db.enqueue_review(conn, ReviewRow(track_id=tid, confidence=0.9))
        assert r1 == r2  # same row updated, not duplicated
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM review_queue WHERE track_id = ?", (tid,)
        ).fetchone()["c"]
    assert count == 1


def test_foreign_key_cascade_deletes_review(db_path: Path, make_track):
    with db.connect(db_path) as conn:
        tid = db.add_track(conn, make_track())
        db.enqueue_review(conn, ReviewRow(track_id=tid, confidence=0.3))
        conn.execute("DELETE FROM tracks WHERE id = ?", (tid,))
        remaining = conn.execute("SELECT COUNT(*) AS c FROM review_queue").fetchone()
    assert remaining["c"] == 0

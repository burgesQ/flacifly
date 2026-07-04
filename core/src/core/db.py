"""SQLite persistence layer: dedup (``tracks``) + review queue (``review_queue``).

Raw ``sqlite3`` (no ORM — lean on a Pi), WAL journaling, idempotent :func:`init_db`.
Timestamps are passed in by callers (ISO8601 strings), never generated deep here.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from .types_ import PathLike, ReviewRow, TrackRow

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
  id            INTEGER PRIMARY KEY,
  source        TEXT NOT NULL,
  source_id     TEXT NOT NULL,
  source_url    TEXT,
  target_dir    TEXT NOT NULL,
  raw_title     TEXT,
  original_path TEXT,
  flac_path     TEXT,
  status        TEXT NOT NULL DEFAULT 'downloaded',
  embedded_json TEXT,
  downloaded_at TEXT NOT NULL,
  UNIQUE(source, source_id)
);

CREATE TABLE IF NOT EXISTS review_queue (
  id             INTEGER PRIMARY KEY,
  track_id       INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
  guessed_artist TEXT,
  guessed_title  TEXT,
  guessed_date   TEXT,
  confidence     REAL NOT NULL,
  resolved       INTEGER NOT NULL DEFAULT 0,
  decision       TEXT,
  UNIQUE(track_id)
);

CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY);
"""


@contextmanager
def connect(db_path: PathLike) -> Iterator[sqlite3.Connection]:
    """Open a connection with WAL + foreign keys; commit on success, else rollback."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables (idempotent) and record the schema version on an open conn."""
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
        (SCHEMA_VERSION,),
    )


def init_db(db_path: PathLike) -> None:
    """Create the DB file (and parent dir) and initialise the schema. Idempotent."""
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        init_schema(conn)


# ---------------------------------------------------------------------------
# tracks
# ---------------------------------------------------------------------------


def _to_track_row(r: sqlite3.Row) -> TrackRow:
    return TrackRow(
        id=r["id"],
        source=r["source"],
        source_id=r["source_id"],
        source_url=r["source_url"],
        target_dir=r["target_dir"],
        raw_title=r["raw_title"],
        original_path=r["original_path"],
        flac_path=r["flac_path"],
        status=r["status"],
        embedded_json=r["embedded_json"],
        downloaded_at=r["downloaded_at"],
    )


def track_exists(conn: sqlite3.Connection, source: str, source_id: str) -> bool:
    """Return True if a track with ``(source, source_id)`` is already recorded."""
    cur = conn.execute(
        "SELECT 1 FROM tracks WHERE source = ? AND source_id = ? LIMIT 1",
        (source, source_id),
    )
    return cur.fetchone() is not None


def add_track(conn: sqlite3.Connection, row: TrackRow) -> int:
    """Insert a track and return its id. Raises ``sqlite3.IntegrityError`` on dup."""
    cur = conn.execute(
        """
        INSERT INTO tracks
          (source, source_id, source_url, target_dir, raw_title,
           original_path, flac_path, status, embedded_json, downloaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row.source,
            row.source_id,
            row.source_url,
            row.target_dir,
            row.raw_title,
            row.original_path,
            row.flac_path,
            row.status,
            row.embedded_json,
            row.downloaded_at,
        ),
    )
    return int(cur.lastrowid or 0)


def get_track(conn: sqlite3.Connection, track_id: int) -> Optional[TrackRow]:
    """Return the track with ``track_id`` or None."""
    cur = conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    r = cur.fetchone()
    return _to_track_row(r) if r else None


def set_status(conn: sqlite3.Connection, track_id: int, status: str) -> None:
    """Update a track's ``status``."""
    conn.execute("UPDATE tracks SET status = ? WHERE id = ?", (status, track_id))


def set_flac_path(conn: sqlite3.Connection, track_id: int, flac_path: str) -> None:
    """Record the transcoded FLAC path for a track."""
    conn.execute("UPDATE tracks SET flac_path = ? WHERE id = ?", (flac_path, track_id))


def set_original_path(
    conn: sqlite3.Connection, track_id: int, original_path: Optional[str]
) -> None:
    """Update (or clear) the lossy source path — e.g. after deleting the original."""
    conn.execute(
        "UPDATE tracks SET original_path = ? WHERE id = ?", (original_path, track_id)
    )


# ---------------------------------------------------------------------------
# review_queue
# ---------------------------------------------------------------------------


def _to_review_row(r: sqlite3.Row) -> ReviewRow:
    return ReviewRow(
        id=r["id"],
        track_id=r["track_id"],
        guessed_artist=r["guessed_artist"],
        guessed_title=r["guessed_title"],
        guessed_date=r["guessed_date"],
        confidence=r["confidence"],
        resolved=bool(r["resolved"]),
        decision=r["decision"],
    )


def enqueue_review(conn: sqlite3.Connection, row: ReviewRow) -> int:
    """Add (or replace) a review-queue entry for a track and return its id."""
    cur = conn.execute(
        """
        INSERT INTO review_queue
          (track_id, guessed_artist, guessed_title, guessed_date, confidence,
           resolved, decision)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(track_id) DO UPDATE SET
          guessed_artist = excluded.guessed_artist,
          guessed_title  = excluded.guessed_title,
          guessed_date   = excluded.guessed_date,
          confidence     = excluded.confidence,
          resolved       = excluded.resolved,
          decision       = excluded.decision
        """,
        (
            row.track_id,
            row.guessed_artist,
            row.guessed_title,
            row.guessed_date,
            row.confidence,
            int(row.resolved),
            row.decision,
        ),
    )
    if cur.lastrowid:
        return int(cur.lastrowid)
    existing = conn.execute(
        "SELECT id FROM review_queue WHERE track_id = ?", (row.track_id,)
    ).fetchone()
    return int(existing["id"])


def pending_reviews(conn: sqlite3.Connection) -> list[ReviewRow]:
    """Return unresolved review-queue rows, oldest first."""
    cur = conn.execute("SELECT * FROM review_queue WHERE resolved = 0 ORDER BY id ASC")
    return [_to_review_row(r) for r in cur.fetchall()]


def resolve_review(
    conn: sqlite3.Connection,
    review_id: int,
    decision: str,
    guessed_artist: Optional[str] = None,
    guessed_title: Optional[str] = None,
    guessed_date: Optional[str] = None,
) -> None:
    """Mark a review row resolved, storing the (possibly edited) final values."""
    conn.execute(
        """
        UPDATE review_queue
           SET resolved = 1,
               decision = ?,
               guessed_artist = COALESCE(?, guessed_artist),
               guessed_title  = COALESCE(?, guessed_title),
               guessed_date   = COALESCE(?, guessed_date)
         WHERE id = ?
        """,
        (decision, guessed_artist, guessed_title, guessed_date, review_id),
    )

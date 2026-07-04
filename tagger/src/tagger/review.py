"""Interactive review of low-confidence identifications.

Walks the SQLite review queue and lets the user accept / edit / skip each guess. The
``prompt`` and ``out`` callables are injected so the flow is fully testable without a
real TTY.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from core import db
from core.types_ import ReviewDecision, ReviewRow, TrackStatus

from .config import TagConfig
from .exit_codes import SUCCESS
from .identify import split_artist_title
from .tags import write_tags

logger = logging.getLogger(__name__)

Prompt = Callable[[str], str]
Out = Callable[[str], None]

_HELP = "[Enter=accept · type 'Artist - Title' to edit · s=skip · q=quit]"


def _decide(
    answer: str, row: ReviewRow
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Map a user answer to (decision, artist, title). decision None means quit."""
    ans = answer.strip()
    if ans in ("q", "quit"):
        return None, None, None
    if ans in ("s", "skip"):
        return ReviewDecision.SKIPPED, None, None
    if ans in ("", "y", "yes"):
        return ReviewDecision.ACCEPTED, row.guessed_artist, row.guessed_title
    artist, title = split_artist_title(ans)
    if artist is None:
        # Treat a bare string as the title, keep the guessed artist.
        return ReviewDecision.EDITED, row.guessed_artist, ans
    return ReviewDecision.EDITED, artist, title


def review_pending(cfg: TagConfig, *, prompt: Prompt = input, out: Out = print) -> int:
    """Interactively resolve every pending review-queue entry."""
    db.init_db(cfg.db_path)
    with db.connect(cfg.db_path) as conn:
        pending = db.pending_reviews(conn)

    if not pending:
        out("Nothing to review.")
        return SUCCESS

    out(f"{len(pending)} track(s) to review. {_HELP}")
    for row in pending:
        with db.connect(cfg.db_path) as conn:
            track = db.get_track(conn, row.track_id)
        if track is None or not track.flac_path:
            logger.warning("review row %s has no FLAC on disk, skipping", row.id)
            continue

        out(
            f"\n{track.raw_title or Path(track.flac_path).name}\n"
            f"  guess: {row.guessed_artist} — {row.guessed_title} "
            f"({row.confidence:.2f})"
        )
        decision, artist, title = _decide(prompt("> "), row)

        if decision is None:
            out("Quit — remaining tracks left in the queue.")
            break
        if decision == ReviewDecision.SKIPPED:
            _resolve(cfg, row, ReviewDecision.SKIPPED, None, None)
            continue

        _apply(cfg, track.id, Path(track.flac_path), artist, title, row.guessed_date)
        _resolve(cfg, row, decision, artist, title)
        out(f"  → {decision}: {artist} — {title}")

    return SUCCESS


def _apply(
    cfg: TagConfig,
    track_id: Optional[int],
    flac: Path,
    artist: Optional[str],
    title: Optional[str],
    date: Optional[str],
) -> None:
    write_tags(flac, artist=artist, title=title, date=date, dry_run=cfg.dry_run)
    if track_id is not None and not cfg.dry_run:
        with db.connect(cfg.db_path) as conn:
            db.set_status(conn, track_id, TrackStatus.TAGGED)


def _resolve(
    cfg: TagConfig,
    row: ReviewRow,
    decision: str,
    artist: Optional[str],
    title: Optional[str],
) -> None:
    if cfg.dry_run or row.id is None:
        logger.debug("[DRY RUN] would resolve review %s as %s", row.id, decision)
        return
    with db.connect(cfg.db_path) as conn:
        db.resolve_review(
            conn, row.id, decision, guessed_artist=artist, guessed_title=title
        )

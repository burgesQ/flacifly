"""The `tag` and `dump` operations: identify tracks and persist metadata.

Confident guesses (``>= confidence_threshold``) are written straight to the FLAC and
the track is marked TAGGED. Uncertain ones are pushed to the SQLite review queue for
``flacifly-tag review`` (step 10). Filesystem/DB glue lives here; parsing lives in
``identify`` / ``resolvers`` and tag I/O in ``tags``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import NamedTuple, Optional

from core import db
from core.types_ import ReviewRow, TrackStatus

from .config import TagConfig
from .resolvers import best_guess
from .tags import clear_tags, read_tags, write_tags
from .types_ import Guess, TrackContext

logger = logging.getLogger(__name__)


class TagSummary(NamedTuple):
    tagged: int
    queued: int
    skipped: int


def iter_flac_files(root: Path) -> list[Path]:
    """Return all ``.flac`` files under ``root`` (recursively), sorted."""
    if root.is_file():
        return [root] if root.suffix.lower() == ".flac" else []
    return sorted(root.rglob("*.flac"))


def _context_for(cfg: TagConfig, flac: Path) -> tuple[TrackContext, Optional[int]]:
    """Build a TrackContext for a FLAC, enriched from its DB row when present."""
    with db.connect(cfg.db_path) as conn:
        track = db.get_track_by_flac_path(conn, str(flac)) or db.get_track_by_flac_path(
            conn, str(flac.resolve())
        )
    if track is not None:
        embedded = json.loads(track.embedded_json) if track.embedded_json else {}
        raw_title = track.raw_title or flac.stem
        return (
            TrackContext(raw_title=raw_title, embedded=embedded, filepath=str(flac)),
            track.id,
        )
    return TrackContext(raw_title=flac.stem, embedded={}, filepath=str(flac)), None


def _apply_confident(
    cfg: TagConfig, flac: Path, guess: Guess, track_id: Optional[int]
) -> None:
    write_tags(
        flac,
        artist=guess.artist,
        title=guess.title,
        date=guess.date,
        dry_run=cfg.dry_run,
    )
    if track_id is not None and not cfg.dry_run:
        with db.connect(cfg.db_path) as conn:
            db.set_status(conn, track_id, TrackStatus.TAGGED)


def _queue_uncertain(
    cfg: TagConfig, flac: Path, guess: Guess, track_id: Optional[int]
) -> bool:
    """Enqueue an uncertain track for review. Returns True if queued."""
    if track_id is None:
        logger.warning(
            "uncertain and not in DB, skipping (no review row): %s", flac.name
        )
        return False
    if cfg.dry_run:
        logger.info("[DRY RUN] would queue for review: %s", flac.name)
        return True
    with db.connect(cfg.db_path) as conn:
        db.enqueue_review(
            conn,
            ReviewRow(
                track_id=track_id,
                confidence=guess.confidence,
                guessed_artist=guess.artist,
                guessed_title=guess.title,
                guessed_date=guess.date,
            ),
        )
    return True


def tag_directory(cfg: TagConfig) -> TagSummary:
    """Identify and tag every FLAC under ``cfg.path``."""
    db.init_db(cfg.db_path)
    files = iter_flac_files(cfg.path)
    logger.info("tagging %d FLAC file(s) under %s", len(files), cfg.path)

    tagged = queued = skipped = 0
    for flac in files:
        ctx, track_id = _context_for(cfg, flac)
        guess = best_guess(ctx)
        if guess.artist and guess.confidence >= cfg.confidence_threshold:
            _apply_confident(cfg, flac, guess, track_id)
            logger.info("tagged: %s — %s / %s", flac.name, guess.artist, guess.title)
            tagged += 1
        elif _queue_uncertain(cfg, flac, guess, track_id):
            queued += 1
        else:
            skipped += 1

    logger.info("done: %d tagged, %d queued, %d skipped", tagged, queued, skipped)
    return TagSummary(tagged=tagged, queued=queued, skipped=skipped)


def dump_directory(cfg: TagConfig) -> int:
    """Print current tags for every FLAC under ``cfg.path``. Returns the file count."""
    files = iter_flac_files(cfg.path)
    for flac in files:
        tags = read_tags(flac)
        print(f"{flac}: {tags}")
    return len(files)


def clear_directory(cfg: TagConfig) -> int:
    """Remove managed tags from every FLAC under ``cfg.path``. Returns the file count."""
    files = iter_flac_files(cfg.path)
    for flac in files:
        clear_tags(flac, dry_run=cfg.dry_run)
    logger.info("cleared tags on %d file(s)", len(files))
    return len(files)

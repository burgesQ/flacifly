"""Low-level FLAC tag I/O via mutagen (Vorbis comments).

Kept deliberately thin and separate from the tagging *operation* (see ``tagging.py``),
mirroring manga_manager's ``epub_metadata`` vs ``editor_full`` split.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Vorbis comment fields we manage.
FIELDS = ("ARTIST", "TITLE", "DATE", "ALBUM", "GENRE")


def read_tags(flac_path: Path) -> dict[str, str]:
    """Return the managed tags currently on a FLAC file (missing keys omitted)."""
    from mutagen.flac import FLAC

    audio = FLAC(str(flac_path))
    out: dict[str, str] = {}
    for field in FIELDS:
        values = audio.get(field)
        if values:
            out[field] = values[0]
    return out


def write_tags(
    flac_path: Path,
    *,
    artist: Optional[str] = None,
    title: Optional[str] = None,
    date: Optional[str] = None,
    album: Optional[str] = None,
    genre: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """Write the provided (non-None) tags to a FLAC file.

    On ``dry_run`` the intended writes are logged and the file is left untouched.
    """
    updates = {
        "ARTIST": artist,
        "TITLE": title,
        "DATE": date,
        "ALBUM": album,
        "GENRE": genre,
    }
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        logger.debug("no tags to write for %s", flac_path)
        return

    if dry_run:
        logger.info("[DRY RUN] would tag %s with %s", flac_path.name, updates)
        return

    from mutagen.flac import FLAC

    audio = FLAC(str(flac_path))
    for key, value in updates.items():
        audio[key] = [value]
    audio.save()
    logger.debug("tagged %s with %s", flac_path.name, updates)

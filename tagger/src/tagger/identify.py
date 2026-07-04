"""Heuristic parsing of a raw video/track title into artist + title.

Pure functions (no I/O). The resolvers in ``tagger.resolvers`` build on these.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Bracketed segments are almost always noise ("[Official Video]", "[HD]", ...).
_BRACKETS = re.compile(r"\[[^\]]*\]")

# Parenthetical noise: only strip parens whose content is a known non-title token.
# Keep musically meaningful parens like "(Radio Edit)", "(Someone Remix)", "(feat. X)".
_NOISE_WORDS = (
    r"official\s*(music\s*)?video|official\s*audio|lyrics?|lyric\s*video|"
    r"visuali[sz]er|hd|hq|4k|full\s*album|out\s*now|free\s*download|"
    r"audio|video|m/?v"
)
_PAREN_NOISE = re.compile(rf"\((?:[^()]*\b(?:{_NOISE_WORDS})\b[^()]*)\)", re.IGNORECASE)

# Artist/title separator: hyphen, en dash, or em dash surrounded by spaces.
_SEP = re.compile(r"\s+[-–—]\s+")

# Collapse repeated whitespace.
_WS = re.compile(r"\s+")


def strip_noise(title: str) -> str:
    """Remove bracketed and known-noise parenthetical segments; collapse spaces."""
    out = _BRACKETS.sub(" ", title)
    out = _PAREN_NOISE.sub(" ", out)
    out = _WS.sub(" ", out).strip()
    # Drop trailing separators left behind by stripping.
    return out.strip(" -–—|")


def split_artist_title(cleaned: str) -> tuple[Optional[str], str]:
    """Split ``Artist - Title`` on the first separator.

    Returns ``(artist, title)``; ``artist`` is None when no clean split is found.
    """
    parts = _SEP.split(cleaned, maxsplit=1)
    if len(parts) == 2:
        artist, title = parts[0].strip(), parts[1].strip()
        if artist and title:
            return artist, title
    return None, cleaned


def year_from_embedded(embedded: dict[str, Any]) -> Optional[str]:
    """Derive a 4-digit year from embedded ``release_year`` / ``upload_date``."""
    year = embedded.get("release_year")
    if year:
        return str(year)[:4]
    upload = embedded.get("upload_date")
    if upload and len(str(upload)) >= 4:
        return str(upload)[:4]
    return None

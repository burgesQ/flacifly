"""Pluggable identification resolvers.

A ``Resolver`` turns a :class:`TrackContext` into a :class:`Guess` (or None). v1 ships
``EmbeddedResolver`` (yt-dlp metadata) and ``HeuristicResolver`` (title parsing). An
``AcoustIDResolver`` (chromaprint + MusicBrainz) can be added here later without changing
callers — it just becomes another entry in ``DEFAULT_RESOLVERS``.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from ..identify import split_artist_title, strip_noise, year_from_embedded
from ..types_ import Guess, TrackContext


@runtime_checkable
class Resolver(Protocol):
    """Something that can propose an identification for a track."""

    def resolve(self, ctx: TrackContext) -> Optional[Guess]: ...


class HeuristicResolver:
    """Parse ``Artist - Title`` out of the (de-noised) raw title."""

    def resolve(self, ctx: TrackContext) -> Optional[Guess]:
        cleaned = strip_noise(ctx.raw_title)
        if not cleaned:
            return None
        artist, title = split_artist_title(cleaned)
        date = year_from_embedded(ctx.embedded)
        if artist:
            return Guess(artist=artist, title=title, date=date, confidence=0.75)
        # No separator: we have a title but no artist — low confidence.
        return Guess(artist=None, title=title, date=date, confidence=0.3)


class EmbeddedResolver:
    """Use yt-dlp embedded ``artist`` / ``track`` fields when present."""

    def resolve(self, ctx: TrackContext) -> Optional[Guess]:
        emb = ctx.embedded
        artist = emb.get("artist") or emb.get("uploader")
        title = emb.get("track") or emb.get("title")
        date = year_from_embedded(emb)
        if emb.get("artist") and emb.get("track"):
            return Guess(artist=artist, title=title, date=date, confidence=0.95)
        if artist and title:
            return Guess(artist=artist, title=title, date=date, confidence=0.5)
        return None


DEFAULT_RESOLVERS: tuple[Resolver, ...] = (EmbeddedResolver(), HeuristicResolver())


def best_guess(
    ctx: TrackContext, resolvers: tuple[Resolver, ...] = DEFAULT_RESOLVERS
) -> Guess:
    """Return the highest-confidence guess across resolvers.

    Falls back to a de-noised title with zero confidence when nothing resolves.
    """
    best: Optional[Guess] = None
    for resolver in resolvers:
        guess = resolver.resolve(ctx)
        if guess is None:
            continue
        if best is None or guess.confidence > best.confidence:
            best = guess
    if best is not None:
        return best
    return Guess(
        artist=None, title=strip_noise(ctx.raw_title) or None, date=None, confidence=0.0
    )

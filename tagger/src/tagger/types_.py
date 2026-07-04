"""Structured types for the tagger package."""

from __future__ import annotations

from typing import Any, NamedTuple, Optional


class Guess(NamedTuple):
    """A candidate identification with a confidence in ``[0, 1]``."""

    artist: Optional[str]
    title: Optional[str]
    date: Optional[str]
    confidence: float


class TrackContext(NamedTuple):
    """Everything a resolver needs to identify one track."""

    raw_title: str
    embedded: dict[str, Any]
    filepath: Optional[str] = None

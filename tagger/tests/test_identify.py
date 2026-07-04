"""Tests for tagger.identify parsing and tagger.resolvers combination logic."""

from __future__ import annotations

import pytest

from tagger.identify import split_artist_title, strip_noise, year_from_embedded
from tagger.resolvers import (
    EmbeddedResolver,
    HeuristicResolver,
    Resolver,
    best_guess,
)
from tagger.types_ import TrackContext


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Artist - Title [Official Video]", "Artist - Title"),
        ("Artist - Title (Official Music Video)", "Artist - Title"),
        ("Artist - Title (HD)", "Artist - Title"),
        ("Artist - Title (Radio Edit)", "Artist - Title (Radio Edit)"),  # kept
        ("Artist - Title (Someone Remix)", "Artist - Title (Someone Remix)"),  # kept
        ("  Spaced   out   title  ", "Spaced out title"),
    ],
)
def test_strip_noise(raw, expected):
    assert strip_noise(raw) == expected


@pytest.mark.parametrize(
    "cleaned,artist,title",
    [
        ("Artist - Title", "Artist", "Title"),
        ("Artist – Title", "Artist", "Title"),  # en dash
        ("Artist — Title", "Artist", "Title"),  # em dash
        ("A - B - C", "A", "B - C"),  # split once
        ("No separator here", None, "No separator here"),
    ],
)
def test_split_artist_title(cleaned, artist, title):
    assert split_artist_title(cleaned) == (artist, title)


def test_year_from_embedded():
    assert year_from_embedded({"release_year": 2019}) == "2019"
    assert year_from_embedded({"upload_date": "20180203"}) == "2018"
    assert year_from_embedded({}) is None


def test_heuristic_resolver_clean_split():
    ctx = TrackContext(raw_title="DJ X - Track One [HD]", embedded={})
    g = HeuristicResolver().resolve(ctx)
    assert g is not None
    assert g.artist == "DJ X" and g.title == "Track One"
    assert g.confidence == 0.75


def test_heuristic_resolver_no_separator_low_confidence():
    g = HeuristicResolver().resolve(TrackContext(raw_title="Just A Title", embedded={}))
    assert g is not None
    assert g.artist is None and g.title == "Just A Title"
    assert g.confidence == 0.3


def test_embedded_resolver_strong_when_artist_and_track():
    ctx = TrackContext(
        raw_title="whatever",
        embedded={"artist": "Real Artist", "track": "Real Track", "release_year": 2020},
    )
    g = EmbeddedResolver().resolve(ctx)
    assert g is not None
    assert (g.artist, g.title, g.date) == ("Real Artist", "Real Track", "2020")
    assert g.confidence == 0.95


def test_embedded_resolver_none_without_fields():
    assert EmbeddedResolver().resolve(TrackContext(raw_title="x", embedded={})) is None


def test_best_guess_prefers_embedded_over_heuristic():
    ctx = TrackContext(
        raw_title="Uploader - Something",
        embedded={"artist": "Real", "track": "Song"},
    )
    g = best_guess(ctx)
    assert g.artist == "Real" and g.title == "Song"
    assert g.confidence == 0.95


def test_best_guess_falls_back_to_heuristic():
    ctx = TrackContext(raw_title="DJ - Banger [Official Video]", embedded={})
    g = best_guess(ctx)
    assert g.artist == "DJ" and g.title == "Banger"


def test_best_guess_zero_confidence_fallback():
    g = best_guess(TrackContext(raw_title="[Official Video]", embedded={}))
    assert g.confidence == 0.0
    assert g.artist is None


def test_resolvers_satisfy_protocol():
    assert isinstance(HeuristicResolver(), Resolver)
    assert isinstance(EmbeddedResolver(), Resolver)

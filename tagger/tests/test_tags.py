"""Tests for tagger.tags: FLAC tag read/write round-trip via mutagen."""

from __future__ import annotations

from pathlib import Path

from tagger.tags import read_tags, write_tags


def test_write_then_read_round_trip(make_flac):
    flac: Path = make_flac()
    write_tags(flac, artist="DJ X", title="Track One", date="2019")
    tags = read_tags(flac)
    assert tags["ARTIST"] == "DJ X"
    assert tags["TITLE"] == "Track One"
    assert tags["DATE"] == "2019"


def test_write_ignores_none_fields(make_flac):
    flac: Path = make_flac()
    write_tags(flac, artist="Only Artist")
    tags = read_tags(flac)
    assert tags["ARTIST"] == "Only Artist"
    assert "TITLE" not in tags


def test_dry_run_writes_nothing(make_flac):
    flac: Path = make_flac()
    write_tags(flac, artist="Ghost", title="Nope", dry_run=True)
    assert read_tags(flac) == {}


def test_fresh_fixture_has_no_managed_tags(make_flac):
    assert read_tags(make_flac()) == {}

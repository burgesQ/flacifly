"""Tests for tagger.cli: subcommand dispatch and config validation."""

from __future__ import annotations

from pathlib import Path

from tagger import cli
from tagger.exit_codes import CLI_ERROR, SUCCESS
from tagger.tags import read_tags, write_tags


def test_no_command_returns_cli_error(capsys):
    assert cli.main([]) == CLI_ERROR


def test_nonexistent_path_returns_cli_error(tmp_path):
    rc = cli.main(["tag", str(tmp_path / "nope"), "--db", str(tmp_path / "db")])
    assert rc == CLI_ERROR


def test_tag_end_to_end(make_flac, tmp_path):
    flac: Path = make_flac("Artist - Title.flac", subdir="music")
    rc = cli.main(
        [
            "tag",
            str(tmp_path / "music"),
            "--db",
            str(tmp_path / "db.sqlite"),
            "--confidence-threshold",
            "0.7",
        ]
    )
    assert rc == SUCCESS
    assert read_tags(flac)["ARTIST"] == "Artist"


def test_dump_prints_tags(make_flac, tmp_path, capsys):
    make_flac("song.flac", subdir="music")
    rc = cli.main(
        ["dump", str(tmp_path / "music"), "--db", str(tmp_path / "db.sqlite")]
    )
    assert rc == SUCCESS
    out = capsys.readouterr().out
    assert "song.flac" in out


def test_clear_removes_tags(make_flac, tmp_path):
    flac: Path = make_flac("song.flac", subdir="music")
    write_tags(flac, artist="A", title="B")
    assert read_tags(flac)  # non-empty
    rc = cli.main(
        ["clear", str(tmp_path / "music"), "--db", str(tmp_path / "db.sqlite")]
    )
    assert rc == SUCCESS
    assert read_tags(flac) == {}


def test_review_empty_queue_dispatches(make_flac, tmp_path):
    make_flac("song.flac", subdir="music")
    rc = cli.main(
        ["review", str(tmp_path / "music"), "--db", str(tmp_path / "db.sqlite")]
    )
    assert rc == SUCCESS

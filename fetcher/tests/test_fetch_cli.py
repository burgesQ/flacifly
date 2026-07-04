"""Tests for fetcher.cli: parsing, config validation, and lock handling."""

from __future__ import annotations

import pytest

from fetcher import cli
from fetcher.exit_codes import CLI_ERROR, LOCKED, SUCCESS


@pytest.fixture(autouse=True)
def _isolate_xdg(tmp_path, monkeypatch):
    """Keep default db/lock paths inside tmp so tests never touch $HOME."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


def test_parser_requires_download_root():
    with pytest.raises(SystemExit):
        cli._build_parser().parse_args([])


def test_build_config_requires_url_or_targets_unless_off(tmp_path):
    args = cli._build_parser().parse_args(
        ["--download-root", str(tmp_path), "--mode", "youtube"]
    )
    with pytest.raises(cli._CLIError):
        cli._build_config(args)


def test_build_config_off_is_ok(tmp_path):
    args = cli._build_parser().parse_args(["--download-root", str(tmp_path)])
    cfg = cli._build_config(args)
    assert cfg.mode == "off"
    assert cfg.keep_original is True


def test_build_config_no_keep_original(tmp_path):
    args = cli._build_parser().parse_args(
        [
            "--download-root",
            str(tmp_path),
            "--url",
            "u",
            "--no-keep-original",
            "--mode",
            "all",
        ]
    )
    cfg = cli._build_config(args)
    assert cfg.keep_original is False


def test_main_validation_error_returns_cli_error(tmp_path):
    rc = cli.main(["--download-root", str(tmp_path), "--mode", "youtube"])
    assert rc == CLI_ERROR


def test_main_mode_off_returns_success(tmp_path):
    rc = cli.main(["--download-root", str(tmp_path)])
    assert rc == SUCCESS


def test_main_returns_locked_when_lock_held(tmp_path):
    from core.locking import job_lock

    lock_dir = tmp_path / "state" / "flacifly" / "locks"
    # Hold the fetch lock, then invoke main which should refuse.
    with job_lock(lock_dir, "fetch"):
        rc = cli.main(["--download-root", str(tmp_path)])
    assert rc == LOCKED

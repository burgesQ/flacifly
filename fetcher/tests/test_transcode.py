"""Tests for fetcher.transcode (FFmpeg runner is mocked; no real ffmpeg)."""

from __future__ import annotations

from pathlib import Path

from fetcher import transcode as tc


def _touch(path: Path, content: str = "audio") -> Path:
    path.write_text(content)
    return path


def test_build_ffmpeg_cmd():
    cmd = tc.build_ffmpeg_cmd(Path("/a/x.opus"), Path("/a/x.flac"), 8)
    assert cmd[0] == "ffmpeg"
    assert "-c:a" in cmd and "flac" in cmd
    assert cmd[cmd.index("-compression_level") + 1] == "8"
    assert cmd[cmd.index("-map_metadata") + 1] == "0"
    assert cmd[-1] == "/a/x.flac"


def test_flac_path_for():
    assert tc.flac_path_for(Path("/a/song.opus")) == Path("/a/song.flac")


def test_transcode_invokes_runner_with_expected_args(tmp_path: Path):
    original = _touch(tmp_path / "song.opus")
    seen: list = []

    def runner(cmd):
        seen.append(cmd)
        Path(cmd[-1]).write_text("flac")  # simulate ffmpeg creating output
        return 0

    flac = tc.transcode_to_flac(original, compression=5, runner=runner)
    assert flac == tmp_path / "song.flac"
    assert seen and seen[0][0] == "ffmpeg"
    assert seen[0][seen[0].index("-compression_level") + 1] == "5"


def test_transcode_idempotent_skip(tmp_path: Path):
    original = _touch(tmp_path / "song.opus")
    flac = _touch(tmp_path / "song.flac")  # already exists and newer
    calls = []

    def runner(cmd):
        calls.append(cmd)
        return 0

    result = tc.transcode_to_flac(original, runner=runner)
    assert result == flac
    assert calls == []  # skipped, runner not called


def test_transcode_failure_returns_none(tmp_path: Path):
    original = _touch(tmp_path / "song.opus")
    result = tc.transcode_to_flac(original, runner=lambda cmd: 1)
    assert result is None


def test_transcode_dry_run_does_not_call_runner(tmp_path: Path):
    original = _touch(tmp_path / "song.opus")
    calls = []
    result = tc.transcode_to_flac(
        original, runner=lambda cmd: calls.append(cmd) or 0, dry_run=True
    )
    assert result == tmp_path / "song.flac"
    assert calls == []
    assert not (tmp_path / "song.flac").exists()

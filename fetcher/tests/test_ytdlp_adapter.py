"""Tests for fetcher.ytdlp_adapter (no network; a fake YoutubeDL is injected)."""

from __future__ import annotations

from pathlib import Path

from fetcher import ytdlp_adapter as ya


class FakeYDL:
    """Minimal stand-in for yt_dlp.YoutubeDL used as a context manager."""

    def __init__(self, opts, probe_info=None, dl_info=None, calls=None):
        self.opts = opts
        self._probe_info = probe_info
        self._dl_info = dl_info
        self._calls = calls if calls is not None else []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=False):
        self._calls.append((url, download))
        return self._dl_info if download else self._probe_info

    def prepare_filename(self, info):
        return f"/downloads/{info.get('title', 'x')}.{info.get('ext', 'opus')}"


def test_build_opts_keeps_source_no_audio_extraction(tmp_path: Path):
    opts = ya.build_ydl_opts(
        tmp_path / "YouTube", archive_path=tmp_path / ".dl", cookiefile=tmp_path / "c"
    )
    assert opts["format"] == "bestaudio/best"
    assert opts["writethumbnail"] is True
    assert opts["noplaylist"] is False
    assert opts["download_archive"].endswith(".dl")
    assert opts["cookiefile"].endswith("c")
    assert "%(title)s.%(ext)s" in opts["outtmpl"]["default"]
    # We must NOT extract audio here (that would delete the lossless-container source).
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" not in keys
    assert "FFmpegMetadata" in keys


def test_source_of_normalisation():
    assert ya._source_of({"extractor_key": "Youtube"}) == "youtube"
    assert ya._source_of({"ie_key": "SoundcloudPlaylist"}) == "soundcloud"
    assert ya._source_of({"extractor": "vimeo"}) == "vimeo"
    assert ya._source_of({}) == "unknown"


def test_iter_entries_flattens_nested():
    info = {"entries": [{"id": "a"}, {"entries": [{"id": "b"}, {"id": "c"}]}]}
    ids = [e["id"] for e in ya._iter_entries(info)]
    assert ids == ["a", "b", "c"]


def test_probe_returns_entry_infos():
    probe_info = {
        "entries": [
            {"id": "1", "title": "A - B", "url": "u1", "ie_key": "Youtube"},
            {"id": "2", "title": "C - D", "url": "u2", "ie_key": "Youtube"},
        ]
    }
    calls: list = []
    entries = ya.probe(
        "playlist",
        {},
        ydl_factory=lambda o: FakeYDL(o, probe_info=probe_info, calls=calls),
    )
    assert [e.source_id for e in entries] == ["1", "2"]
    assert entries[0].webpage_url == "u1"
    assert calls == [("playlist", False)]


def test_download_entry_returns_filepath():
    dl_info = {"id": "1", "title": "A - B", "ext": "m4a", "extractor_key": "Youtube"}
    calls: list = []
    result = ya.download_entry(
        "u1", {}, ydl_factory=lambda o: FakeYDL(o, dl_info=dl_info, calls=calls)
    )
    assert result is not None
    assert result.entry.source_id == "1"
    assert result.filepath == "/downloads/A - B.m4a"
    assert calls == [("u1", True)]


def test_download_entry_uses_requested_downloads_filepath():
    dl_info = {
        "id": "1",
        "title": "T",
        "extractor_key": "Youtube",
        "requested_downloads": [{"filepath": "/real/path.opus"}],
    }
    result = ya.download_entry(
        "u", {}, ydl_factory=lambda o: FakeYDL(o, dl_info=dl_info)
    )
    assert result is not None
    assert result.filepath == "/real/path.opus"

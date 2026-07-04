"""Tests for fetcher.downloader: targets, mode gating, dedup, dry-run."""

from __future__ import annotations

from pathlib import Path

from core import db
from core.types_ import TrackRow
from fetcher import downloader as dl
from fetcher.config import MODE_ALL, MODE_OFF, MODE_YOUTUBE, FetchConfig
from fetcher.exit_codes import SUCCESS


class FakeYDL:
    def __init__(self, factory, opts):
        self.factory = factory
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=False):
        if not download:
            return self.factory.probe_info
        self.factory.downloaded.append(url)
        return self.factory.dl_infos[url]

    def prepare_filename(self, info):
        base = self.factory.download_dir
        return str(base / f"{info.get('title', 'x')}.{info.get('ext', 'opus')}")


class FakeFactory:
    def __init__(self, probe_info, dl_infos, download_dir: Path):
        self.probe_info = probe_info
        self.dl_infos = dl_infos
        self.download_dir = download_dir
        self.downloaded: list[str] = []

    def __call__(self, opts):
        return FakeYDL(self, opts)


def _cfg(tmp_path: Path, **kw) -> FetchConfig:
    defaults = dict(
        download_root=tmp_path / "dl",
        db_path=tmp_path / "db.sqlite",
        lock_dir=tmp_path / "locks",
        mode=MODE_YOUTUBE,
        url="https://www.youtube.com/playlist?list=X",
    )
    defaults.update(kw)
    return FetchConfig(**defaults)  # type: ignore[arg-type]


def test_read_targets(tmp_path: Path):
    f = tmp_path / "targets.conf"
    f.write_text(
        "# a comment\n"
        "YouTube https://youtube.com/playlist?list=A\n"
        "\n"
        "SoundCloud   https://soundcloud.com/x\n"
        "malformed_line_without_url\n"
    )
    targets = dl.read_targets(f)
    assert [t.name for t in targets] == ["YouTube", "SoundCloud"]
    assert targets[0].url == "https://youtube.com/playlist?list=A"


def test_url_source_and_mode_gating():
    assert dl._url_source("https://soundcloud.com/x") == "soundcloud"
    assert dl._url_source("https://music.youtube.com/x") == "youtube"
    assert dl._mode_allows(MODE_OFF, "youtube") is False
    assert dl._mode_allows(MODE_ALL, "soundcloud") is True
    assert dl._mode_allows(MODE_YOUTUBE, "youtube") is True
    assert dl._mode_allows(MODE_YOUTUBE, "soundcloud") is False


# A fake FFmpeg runner that "creates" the FLAC and succeeds (never calls real ffmpeg).
def _fake_runner(cmd):
    Path(cmd[-1]).write_text("flac")
    return 0


def test_run_mode_off_is_noop(tmp_path: Path):
    factory = FakeFactory({"entries": []}, {}, tmp_path)
    rc = dl.run(
        _cfg(tmp_path, mode=MODE_OFF),
        now="2026-01-01T00:00:00Z",
        ydl_factory=factory,
        runner=_fake_runner,
    )
    assert rc == SUCCESS
    assert factory.downloaded == []


def _leaf(id_, title, ext="opus"):
    return {"id": id_, "title": title, "ext": ext, "extractor_key": "Youtube"}


def test_run_dedup_skips_known_and_downloads_new(tmp_path: Path):
    cfg = _cfg(tmp_path)
    db.init_db(cfg.db_path)
    with db.connect(cfg.db_path) as conn:
        db.add_track(
            conn,
            TrackRow(
                source="youtube",
                source_id="1",
                target_dir="_url",
                downloaded_at="2026-01-01T00:00:00Z",
            ),
        )

    probe_info = {
        "entries": [
            {"id": "1", "title": "Known", "url": "wurl1", "ie_key": "Youtube"},
            {"id": "2", "title": "New - Track", "url": "wurl2", "ie_key": "Youtube"},
        ]
    }
    factory = FakeFactory(
        probe_info, {"wurl2": _leaf("2", "New - Track")}, tmp_path / "dl" / "_url"
    )

    rc = dl.run(
        cfg, now="2026-07-04T00:00:00Z", ydl_factory=factory, runner=_fake_runner
    )
    assert rc == SUCCESS
    # Only the not-yet-seen entry was downloaded.
    assert factory.downloaded == ["wurl2"]
    with db.connect(cfg.db_path) as conn:
        assert db.track_exists(conn, "youtube", "2")
        row = conn.execute(
            "SELECT status, flac_path FROM tracks WHERE source_id = '2'"
        ).fetchone()
        count = conn.execute("SELECT COUNT(*) AS c FROM tracks").fetchone()["c"]
    assert count == 2
    assert row["status"] == "transcoded"
    assert row["flac_path"].endswith(".flac")


def test_run_deletes_original_when_not_keep(tmp_path: Path):
    cfg = _cfg(tmp_path, keep_original=False)
    # The fake download reports a real file so the delete path can run.
    original = tmp_path / "dl" / "_url" / "Song - Title.opus"
    original.parent.mkdir(parents=True)
    original.write_text("audio")

    probe_info = {
        "entries": [
            {"id": "5", "title": "Song - Title", "url": "w5", "ie_key": "Youtube"}
        ]
    }

    class FileFactory(FakeFactory):
        def __init__(self):
            super().__init__(
                probe_info, {"w5": _leaf("5", "Song - Title")}, original.parent
            )

        # Override prepare_filename via the leaf's requested_downloads path.
        def __call__(self, opts):
            ydl = FakeYDL(self, opts)
            self.dl_infos["w5"]["requested_downloads"] = [{"filepath": str(original)}]
            return ydl

    rc = dl.run(cfg, now="now", ydl_factory=FileFactory(), runner=_fake_runner)
    assert rc == SUCCESS
    assert not original.exists()  # deleted
    with db.connect(cfg.db_path) as conn:
        row = conn.execute(
            "SELECT original_path, flac_path FROM tracks WHERE source_id = '5'"
        ).fetchone()
    assert row["original_path"] is None
    assert row["flac_path"].endswith(".flac")


def test_run_threaded_processes_all_entries(tmp_path: Path):
    cfg = _cfg(tmp_path, nb_worker=4)
    probe_info = {
        "entries": [
            {"id": str(i), "title": f"T{i}", "url": f"w{i}", "ie_key": "Youtube"}
            for i in range(5)
        ]
    }
    dl_infos = {f"w{i}": _leaf(str(i), f"T{i}") for i in range(5)}
    factory = FakeFactory(probe_info, dl_infos, tmp_path / "dl" / "_url")
    rc = dl.run(cfg, now="now", ydl_factory=factory, runner=_fake_runner)
    assert rc == SUCCESS
    assert sorted(factory.downloaded) == [f"w{i}" for i in range(5)]
    with db.connect(cfg.db_path) as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM tracks").fetchone()["c"]
    assert count == 5


def test_run_dry_run_downloads_nothing(tmp_path: Path):
    cfg = _cfg(tmp_path, dry_run=True)
    probe_info = {
        "entries": [{"id": "9", "title": "X", "url": "w9", "ie_key": "Youtube"}]
    }
    factory = FakeFactory(probe_info, {}, tmp_path / "dl" / "_url")
    rc = dl.run(cfg, now="2026-07-04T00:00:00Z", ydl_factory=factory)
    assert rc == SUCCESS
    assert factory.downloaded == []
    with db.connect(cfg.db_path) as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM tracks").fetchone()["c"]
    assert count == 0

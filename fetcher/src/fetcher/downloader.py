"""Download orchestration: resolve targets, dedup, download, transcode, record.

Per-target entries are processed with a ``ThreadPoolExecutor`` (``--nb-worker``,
default 1 — FFmpeg is the CPU cost on a Pi). Individual download/transcode failures
are counted (not fatal): reruns skip completed tracks via the DB dedup + yt-dlp
download-archive, so a partial run is safe to repeat.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import re
from pathlib import Path
from typing import Any

from core import db
from core.types_ import TrackRow, TrackStatus

from .config import MODE_ALL, MODE_OFF, FetchConfig
from .exit_codes import DOWNLOAD_ERROR, SUCCESS
from .transcode import Runner
from .transcode import _default_runner as _default_transcode_runner
from .transcode import transcode_to_flac
from .types_ import DownloadedEntry, EntryInfo, FetchTarget
from .ytdlp_adapter import (
    YdlFactory,
    _default_ydl_factory,
    build_ydl_opts,
    download_entry,
    probe,
)

logger = logging.getLogger(__name__)


def read_targets(path: Path) -> list[FetchTarget]:
    """Parse a ``targets.conf`` (``Name  URL`` per line; ``#`` and blanks ignored)."""
    targets: list[FetchTarget] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            logger.warning("ignoring malformed targets line: %r", raw)
            continue
        targets.append(FetchTarget(name=parts[0], url=parts[1]))
    return targets


def _cookies_ok(path: Path) -> bool:
    """Validate a cookies file up front (Netscape format), with actionable errors."""
    from http.cookiejar import LoadError, MozillaCookieJar

    if not path.exists():
        logger.error("cookies file not found: %s", path)
        return False
    try:
        MozillaCookieJar(str(path)).load()
    except LoadError as e:
        logger.error(
            "invalid cookies file %s: %s — export it in Netscape format "
            "(e.g. a 'Get cookies.txt' browser extension)",
            path,
            e,
        )
        return False
    except OSError as e:
        logger.error("cannot read cookies file %s: %s", path, e)
        return False
    return True


# A YouTube "uploads" playlist (list=UU + 22-char channel suffix) only serves 100
# items via the playlist endpoint; the channel /videos tab paginates fully. Match the
# classic UU id exactly (22 chars) so UULF/UUSH/UUPS variants are left untouched.
_UPLOADS_RE = re.compile(r"[?&]list=UU([0-9A-Za-z_-]{22})(?=&|$)")


def _normalize_url(url: str) -> str:
    """Rewrite a YouTube uploads-playlist URL to the channel videos tab (full list)."""
    m = _UPLOADS_RE.search(url)
    if not m:
        return url
    channel = "UC" + m.group(1)
    rewritten = f"https://www.youtube.com/channel/{channel}/videos"
    logger.info("uploads playlist → channel videos tab (full list): %s", rewritten)
    return rewritten


def _url_source(url: str) -> str:
    """Coarse source label from a URL, for mode gating before probing."""
    return "soundcloud" if "soundcloud" in url.lower() else "youtube"


def _mode_allows(mode: str, source: str) -> bool:
    if mode == MODE_OFF:
        return False
    if mode == MODE_ALL:
        return True
    return mode == source


def _resolve_targets(cfg: FetchConfig) -> list[FetchTarget]:
    """Build the target list from ``--url`` or the targets file."""
    if cfg.url:
        return [FetchTarget(name="_url", url=cfg.url)]
    if cfg.targets_file and cfg.targets_file.exists():
        return read_targets(cfg.targets_file)
    return []


def _embedded_json(entry: EntryInfo, info: dict[str, Any]) -> str:
    """Serialise a small, stable subset of yt-dlp metadata for later tagging."""
    keep = ("uploader", "artist", "track", "album", "release_year", "upload_date")
    payload = {"title": entry.title, **{k: info.get(k) for k in keep if info.get(k)}}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _record_download(
    cfg: FetchConfig, target: FetchTarget, dl: DownloadedEntry, now: str
) -> int:
    """Insert the downloaded track and return its DB id."""
    with db.connect(cfg.db_path) as conn:
        return db.add_track(
            conn,
            TrackRow(
                source=dl.entry.source,
                source_id=dl.entry.source_id,
                source_url=dl.entry.webpage_url or None,
                target_dir=target.name,
                raw_title=dl.entry.title or None,
                original_path=dl.filepath,
                status=TrackStatus.DOWNLOADED,
                embedded_json=_embedded_json(dl.entry, dl.info),
                downloaded_at=now,
            ),
        )


def _transcode_and_finalize(
    cfg: FetchConfig, track_id: int, dl: DownloadedEntry, runner: Runner
) -> None:
    """Transcode the downloaded original to FLAC and update the track's DB state."""
    original = Path(dl.filepath)
    flac = transcode_to_flac(
        original, compression=cfg.flac_compression, runner=runner, dry_run=cfg.dry_run
    )
    if flac is None:
        with db.connect(cfg.db_path) as conn:
            db.set_status(conn, track_id, TrackStatus.FAILED)
        return

    with db.connect(cfg.db_path) as conn:
        db.set_flac_path(conn, track_id, str(flac))
        db.set_status(conn, track_id, TrackStatus.TRANSCODED)

    if not cfg.keep_original and original.exists() and original != flac:
        original.unlink()
        with db.connect(cfg.db_path) as conn:
            db.set_original_path(conn, track_id, None)
        logger.debug("removed original (keep_original=False): %s", original)


def _process_entry(
    cfg: FetchConfig,
    target: FetchTarget,
    entry: EntryInfo,
    now: str,
    opts: dict[str, Any],
    ydl_factory: YdlFactory,
    runner: Runner,
) -> int:
    """Download + transcode one entry. Returns 1 on error, 0 on success/skip."""
    with db.connect(cfg.db_path) as conn:
        if db.track_exists(conn, entry.source, entry.source_id):
            logger.debug("skip (already have): %s [%s]", entry.title, entry.source_id)
            return 0

    if cfg.dry_run:
        logger.info("[DRY RUN] would download: %s", entry.title or entry.webpage_url)
        return 0

    dl_dir = cfg.download_root / target.name
    dl_dir.mkdir(parents=True, exist_ok=True)
    dl = download_entry(entry.webpage_url, opts, ydl_factory)
    if dl is None:
        return 1

    track_id = _record_download(cfg, target, dl, now)
    _transcode_and_finalize(cfg, track_id, dl, runner)
    logger.info("done: %s", dl.entry.title or dl.filepath)
    return 0


def _process_target(
    cfg: FetchConfig,
    target: FetchTarget,
    now: str,
    ydl_factory: YdlFactory,
    runner: Runner,
) -> int:
    """Probe a target and process its entries (threaded when nb_worker > 1)."""
    dl_dir = cfg.download_root / target.name
    opts = build_ydl_opts(
        dl_dir,
        archive_path=dl_dir / ".downloaded",
        cookiefile=cfg.cookies,
        quiet=not cfg.verbose,
    )
    entries = probe(_normalize_url(target.url), opts, ydl_factory)
    logger.info("target %s: %d ent/track(s)", target.name, len(entries))

    def work(entry: EntryInfo) -> int:
        return _process_entry(cfg, target, entry, now, opts, ydl_factory, runner)

    if cfg.nb_worker > 1 and not cfg.dry_run:
        with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.nb_worker) as ex:
            return sum(ex.map(work, entries))
    return sum(work(entry) for entry in entries)


def run(
    cfg: FetchConfig,
    *,
    now: str,
    ydl_factory: YdlFactory = _default_ydl_factory,
    runner: Runner = _default_transcode_runner,
) -> int:
    """Run the fetch pipeline. ``now`` is an ISO8601 timestamp supplied by the caller."""
    if cfg.mode == MODE_OFF:
        logger.info("mode=off — nothing to do (safe default)")
        return SUCCESS

    if cfg.cookies is not None and not _cookies_ok(cfg.cookies):
        return DOWNLOAD_ERROR

    targets = _resolve_targets(cfg)
    if not targets:
        logger.error("no targets: pass --url or a readable --targets file")
        return DOWNLOAD_ERROR

    db.init_db(cfg.db_path)

    total_errors = 0
    for target in targets:
        source = _url_source(target.url)
        if not _mode_allows(cfg.mode, source):
            logger.debug(
                "skip target %s (mode=%s, source=%s)", target.name, cfg.mode, source
            )
            continue
        total_errors += _process_target(cfg, target, now, ydl_factory, runner)

    if total_errors:
        logger.error("%d download error(s)", total_errors)
        return DOWNLOAD_ERROR
    return SUCCESS

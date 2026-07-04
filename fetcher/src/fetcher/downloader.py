"""Download orchestration: resolve targets, dedup against the DB, record tracks.

Step-6 scope: sequential download + DB recording. Transcoding to FLAC and threaded
workers are layered on in ``transcode.py`` / the ThreadPoolExecutor path (step 7).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from core import db
from core.types_ import TrackRow, TrackStatus

from .config import MODE_ALL, MODE_OFF, FetchConfig
from .exit_codes import DOWNLOAD_ERROR, SUCCESS
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


def _embedded_json(entry: EntryInfo, info: dict) -> str:
    """Serialise a small, stable subset of yt-dlp metadata for later tagging."""
    keep = ("uploader", "artist", "track", "album", "release_year", "upload_date")
    payload = {"title": entry.title, **{k: info.get(k) for k in keep if info.get(k)}}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _record_download(
    cfg: FetchConfig, target: FetchTarget, dl: DownloadedEntry, now: str
) -> None:
    with db.connect(cfg.db_path) as conn:
        db.add_track(
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


def _process_target(
    cfg: FetchConfig, target: FetchTarget, now: str, ydl_factory: YdlFactory
) -> int:
    """Probe a target, download not-yet-seen entries, record them. Returns error count."""
    dl_dir = cfg.download_root / target.name
    opts = build_ydl_opts(
        dl_dir,
        archive_path=dl_dir / ".downloaded",
        cookiefile=cfg.cookies,
        quiet=not cfg.verbose,
    )
    entries = probe(target.url, opts, ydl_factory)
    logger.info("target %s: %d ent/track(s)", target.name, len(entries))

    errors = 0
    for entry in entries:
        with db.connect(cfg.db_path) as conn:
            already = db.track_exists(conn, entry.source, entry.source_id)
        if already:
            logger.debug("skip (already have): %s [%s]", entry.title, entry.source_id)
            continue
        if cfg.dry_run:
            logger.info(
                "[DRY RUN] would download: %s", entry.title or entry.webpage_url
            )
            continue

        dl_dir.mkdir(parents=True, exist_ok=True)
        dl = download_entry(entry.webpage_url, opts, ydl_factory)
        if dl is None:
            errors += 1
            continue
        _record_download(cfg, target, dl, now)
        logger.info("downloaded: %s", dl.entry.title or dl.filepath)
    return errors


def run(
    cfg: FetchConfig,
    *,
    now: str,
    ydl_factory: YdlFactory = _default_ydl_factory,
) -> int:
    """Run the fetch pipeline. ``now`` is an ISO8601 timestamp supplied by the caller."""
    if cfg.mode == MODE_OFF:
        logger.info("mode=off — nothing to do (safe default)")
        return SUCCESS

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
        total_errors += _process_target(cfg, target, now, ydl_factory)

    if total_errors:
        logger.error("%d download error(s)", total_errors)
        return DOWNLOAD_ERROR
    return SUCCESS

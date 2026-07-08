"""Thin, testable wrapper around ``yt_dlp.YoutubeDL``.

The ``YoutubeDL`` instance is created by an injectable factory so tests can supply a
fake and never touch the network. We deliberately do **not** enable audio extraction
here — the native best-audio file is kept and transcoded to FLAC separately (see
``transcode.py``), so the lossless source survives.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, ContextManager, Iterator, Optional, cast

from .types_ import DownloadedEntry, EntryInfo

logger = logging.getLogger(__name__)

# A factory turning an options dict into a YoutubeDL context manager.
YdlFactory = Callable[[dict[str, Any]], ContextManager[Any]]


def _default_ydl_factory(opts: dict[str, Any]) -> ContextManager[Any]:
    from yt_dlp import YoutubeDL  # imported lazily so tests need not touch the network

    return cast(ContextManager[Any], YoutubeDL(opts))


def build_ydl_opts(
    download_dir: Path,
    *,
    archive_path: Optional[Path] = None,
    cookiefile: Optional[Path] = None,
    quiet: bool = True,
    sleep_requests: float = 0.0,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the yt-dlp options dict for best-audio download (keeps the source).

    Mirrors the old ``youtube-dl.conf``: best audio, per-dir download archive,
    playlist enabled, thumbnail written, geo-bypass, ignore errors. ``sleep_requests``
    (seconds) throttles HTTP requests to avoid YouTube rate-limiting.
    """
    opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": {"default": str(download_dir / "%(title)s.%(ext)s")},
        "ignoreerrors": True,
        "geo_bypass": True,
        "noplaylist": False,
        "writethumbnail": True,
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": True,
        "postprocessors": [{"key": "FFmpegMetadata", "add_metadata": True}],
    }
    if archive_path is not None:
        opts["download_archive"] = str(archive_path)
    if cookiefile is not None:
        opts["cookiefile"] = str(cookiefile)
    if sleep_requests > 0:
        # Equivalent to yt-dlp's `-t sleep` recommendation on rate-limit errors.
        opts["sleep_interval_requests"] = sleep_requests
    if extra:
        opts.update(extra)
    return opts


def _source_of(info: dict[str, Any]) -> str:
    """Normalise yt-dlp's extractor name to a coarse source label."""
    key = (
        info.get("extractor_key") or info.get("ie_key") or info.get("extractor") or ""
    ).lower()
    if "youtube" in key:
        return "youtube"
    if "soundcloud" in key:
        return "soundcloud"
    return key or "unknown"


def _iter_entries(info: Optional[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Flatten a (possibly nested) playlist info dict into leaf entries."""
    if not info:
        return
    entries = info.get("entries")
    if entries is not None:
        for e in entries:
            yield from _iter_entries(e)
    else:
        yield info


def _to_entry_info(info: dict[str, Any]) -> EntryInfo:
    return EntryInfo(
        source=_source_of(info),
        source_id=str(info.get("id", "")),
        title=str(info.get("title", "")),
        webpage_url=str(
            info.get("webpage_url") or info.get("original_url") or info.get("url") or ""
        ),
        ext=info.get("ext"),
    )


def probe(
    url: str,
    opts: dict[str, Any],
    ydl_factory: YdlFactory = _default_ydl_factory,
) -> list[EntryInfo]:
    """Extract metadata for ``url`` without downloading; return leaf entries.

    Never raises: a hard error (bad cookies, network, geo) is logged and yields ``[]``.
    """
    probe_opts = dict(opts)
    probe_opts["extract_flat"] = "in_playlist"
    try:
        with ydl_factory(probe_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:  # noqa: BLE001 - one bad target must not abort the batch
        logger.error("probe failed for %s: %s", url, e)
        return []
    return [_to_entry_info(e) for e in _iter_entries(info)]


def _entry_filepath(ydl: Any, info: dict[str, Any]) -> str:
    reqs = info.get("requested_downloads")
    if reqs and reqs[0].get("filepath"):
        return str(reqs[0]["filepath"])
    return str(ydl.prepare_filename(info))


def download_entry(
    webpage_url: str,
    opts: dict[str, Any],
    ydl_factory: YdlFactory = _default_ydl_factory,
) -> Optional[DownloadedEntry]:
    """Download a single entry URL; return its result or None on failure.

    Never raises: a hard error (bad cookies, network, unavailable format) is logged
    and yields ``None`` so the batch continues.
    """
    try:
        with ydl_factory(opts) as ydl:
            info = ydl.extract_info(webpage_url, download=True)
            if not info:
                logger.error("no info returned for %s", webpage_url)
                return None
            # A single-video URL returns a leaf; be defensive about playlist wrapping.
            leaf = next(_iter_entries(info), info)
            filepath = _entry_filepath(ydl, leaf)
    except Exception as e:  # noqa: BLE001 - one bad entry must not abort the batch
        logger.error("download failed for %s: %s", webpage_url, e)
        return None
    return DownloadedEntry(entry=_to_entry_info(leaf), filepath=filepath, info=leaf)

"""Structured types for the fetcher package."""

from __future__ import annotations

from typing import Any, NamedTuple, Optional


class FetchTarget(NamedTuple):
    """A download target from ``targets.conf``: a logical name and a URL."""

    name: str
    url: str


class EntryInfo(NamedTuple):
    """Metadata for one playlist entry / single track (from a probe)."""

    source: str
    source_id: str
    title: str
    webpage_url: str
    ext: Optional[str] = None


class DownloadedEntry(NamedTuple):
    """Result of downloading one entry: its metadata, file path, and raw info."""

    entry: EntryInfo
    filepath: str
    info: dict[str, Any]

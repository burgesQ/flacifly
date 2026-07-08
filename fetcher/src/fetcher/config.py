"""Runtime configuration for a fetch invocation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.config import BaseConfig

# Download modes: which sources to process. "off" is a safe no-op default.
MODE_ALL = "all"
MODE_YOUTUBE = "youtube"
MODE_SOUNDCLOUD = "soundcloud"
MODE_OFF = "off"
MODES = (MODE_ALL, MODE_YOUTUBE, MODE_SOUNDCLOUD, MODE_OFF)


@dataclass(kw_only=True)
class FetchConfig(BaseConfig):
    """Options for downloading + transcoding audio."""

    download_root: Path
    targets_file: Optional[Path] = None
    ytdlp_conf: Optional[Path] = None
    cookies: Optional[Path] = None
    mode: str = MODE_OFF
    url: Optional[str] = None
    keep_original: bool = True
    flac_compression: int = 8
    sleep_requests: float = 0.0

"""Base runtime configuration shared by the flacifly tools.

Per-package configs (``fetcher.config.FetchConfig`` / ``tagger.config.TagConfig``)
extend :class:`BaseConfig`. ``kw_only=True`` lets subclasses add required fields
without dataclass default-ordering conflicts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def default_db_path() -> Path:
    """Return the default SQLite DB location (respects ``XDG_DATA_HOME``)."""
    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "flacifly" / "flacifly.db"


def default_lock_dir() -> Path:
    """Return the default lock directory (respects ``XDG_STATE_HOME``)."""
    base = os.environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path.home() / ".local" / "state"
    return root / "flacifly" / "locks"


@dataclass(kw_only=True)
class BaseConfig:
    """Options common to every flacifly invocation."""

    db_path: Path = field(default_factory=default_db_path)
    lock_dir: Path = field(default_factory=default_lock_dir)
    nb_worker: int = 1
    dry_run: bool = False
    verbose: bool = False
    loglevel: Optional[str] = None

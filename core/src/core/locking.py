"""Filesystem lock-dir mutual exclusion.

Prevents overlapping scheduled runs (a fetch starting while a previous fetch/tag is
still working). Uses ``Path.mkdir`` which is atomic on POSIX — creating an existing
directory raises ``FileExistsError``, so the lock is race-free without extra deps.

Ported in spirit from ``sosound-tools`` per-job lock directories.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .types_ import PathLike

logger = logging.getLogger(__name__)


class LockError(RuntimeError):
    """Raised when a lock is already held by another run."""


def _lock_path(lock_dir: PathLike, name: str) -> Path:
    return Path(lock_dir) / f"{name}.lock"


def is_locked(lock_dir: PathLike, name: str) -> bool:
    """Return True if the named lock is currently held."""
    return _lock_path(lock_dir, name).exists()


@contextmanager
def job_lock(lock_dir: PathLike, name: str) -> Iterator[Path]:
    """Acquire the named lock for the duration of the ``with`` block.

    Raises :class:`LockError` if the lock is already held. The lock directory is
    always removed on exit, including when the body raises.
    """
    Path(lock_dir).mkdir(parents=True, exist_ok=True)
    path = _lock_path(lock_dir, name)
    try:
        path.mkdir()
    except FileExistsError as e:
        raise LockError(f"lock '{name}' already held ({path})") from e

    logger.debug("acquired lock: %s", path)
    try:
        yield path
    finally:
        try:
            path.rmdir()
            logger.debug("released lock: %s", path)
        except OSError as e:  # pragma: no cover - best-effort cleanup
            logger.warning("could not release lock %s: %s", path, e)

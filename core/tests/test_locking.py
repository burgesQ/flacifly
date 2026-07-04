"""Tests for core.locking: acquire/release, contention, and cleanup on error."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.locking import LockError, is_locked, job_lock


def test_acquire_and_release(tmp_path: Path):
    assert not is_locked(tmp_path, "fetch")
    with job_lock(tmp_path, "fetch"):
        assert is_locked(tmp_path, "fetch")
    assert not is_locked(tmp_path, "fetch")


def test_double_acquire_raises(tmp_path: Path):
    with job_lock(tmp_path, "fetch"):
        with pytest.raises(LockError):
            with job_lock(tmp_path, "fetch"):
                pass  # pragma: no cover


def test_different_names_do_not_conflict(tmp_path: Path):
    with job_lock(tmp_path, "fetch"):
        with job_lock(tmp_path, "tag"):
            assert is_locked(tmp_path, "fetch")
            assert is_locked(tmp_path, "tag")


def test_lock_released_on_exception(tmp_path: Path):
    with pytest.raises(ValueError):
        with job_lock(tmp_path, "fetch"):
            raise ValueError("boom")
    assert not is_locked(tmp_path, "fetch")
    # Re-acquirable afterwards.
    with job_lock(tmp_path, "fetch"):
        assert is_locked(tmp_path, "fetch")


def test_creates_lock_dir_if_missing(tmp_path: Path):
    lock_root = tmp_path / "does" / "not" / "exist"
    with job_lock(lock_root, "fetch"):
        assert lock_root.exists()

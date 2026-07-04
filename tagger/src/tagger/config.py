"""Runtime configuration for a tag invocation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import BaseConfig


@dataclass(kw_only=True)
class TagConfig(BaseConfig):
    """Options for identifying and writing metadata."""

    path: Path
    confidence_threshold: float = 0.8

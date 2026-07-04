#!/usr/bin/env python3
"""Entry point shim for the flacifly-tag CLI."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the package `src` directory is importable when run as a script.
_pkg_src = str(Path(__file__).resolve().parent.parent)
if _pkg_src not in sys.path:
    sys.path.insert(0, _pkg_src)

from tagger.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

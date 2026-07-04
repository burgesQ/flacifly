# flacifly — Conventions

Python DJ-crate tool: download best-quality audio (YouTube / YT Music / SoundCloud via yt-dlp),
transcode to FLAC (keeping the lossy original), then tag (artist/track). Runs as a oneshot container
on a Raspberry Pi. uv-workspace monorepo of three packages: `core`, `fetcher`, `tagger`.

> ⚠️ FLAC-from-lossy caveat: YouTube/SoundCloud only serve lossy audio. Transcoding to FLAC gives a
> lossless *container*, not more fidelity. We keep the original best-audio file alongside the FLAC.

## Golden rules
- **argparse only** — no click/typer. `main(argv=None) -> int`; entry via `<pkg>.main:main`.
- **`_CLIError` early-exit**: helpers log then `raise _CLIError`; `main()` catches → returns a code.
  Keep `main()` flat (~25 lines) by decomposing into `_build_parser`/`_validate_args`/… helpers.
- **Exit codes**: every package has `exit_codes.py` named constants — never bare integer literals.
- **`--dry-run` mandatory** on every write path (log intent, touch nothing).
- **`pathlib.Path`** for all filesystem ops.
- **Logging**: `logging.getLogger(__name__)`, never `print()` (except intentional interactive prompts
  in `tagger review`). Shared `setup_logging` + `ColorFormatter` (emoji/ANSI) live in `core`; every CLI
  calls it and exposes `--verbose` + `--loglevel`.
- **Types**: `NamedTuple` for structured returns; `TypeAlias` for composite types; a `Config` dataclass
  threaded through the call stack (not loose kwargs). `py.typed` in every package.
- **No secrets in the repo**: cookies file is git-ignored and mounted at runtime.
- Line length **88** (Black). Ruff select `E4,E7,E9,F`. mypy strict on all packages.
- All code/comments/docs in **English**.

## Layout
`core/` shared (logging, db, config, locking, types, exit_codes) — imported by the other two.
`fetcher/` task 1 (download→FLAC). `tagger/` task 2 (metadata + review). `src/` layout everywhere.
Console scripts: `flacifly-fetch = fetcher.main:main`, `flacifly-tag = tagger.main:main`.

## SQLite
Raw `sqlite3`, WAL, single DB file (default `~/.local/share/flacifly/flacifly.db`, `--db` override).
`tracks` = dedup + provenance; `review_queue` = items whose ID is <100% confident, walked by
`flacifly-tag review`. Idempotent `init_db()`. No timestamps generated deep in helpers — pass them in.

## Concurrency
`ThreadPoolExecutor`, `--nb-worker` default 1 (Pi-friendly; FFmpeg is the cost). First failure aborts the
batch (mirror `manga_manager/packer/worker.py` `_run_tasks`). `core.locking` (filesystem lock dir)
prevents overlapping scheduled runs.

## Testing
Root `pytest.ini` is the real config (per-package `[pytest]` tables in pyproject.toml are ignored by
pytest). `tests/` beside `src/`, `test_*.py`. Factory-pattern fixtures in per-package `conftest.py`.
Call `main([...])` directly for coverage; reserve subprocess fixtures for smoke tests. Assert on
`capsys.readouterr().err` (not `caplog` — `setup_logging` clears handlers). Do NOT blanket-add
`__init__.py` to every `tests/` dir (avoids cross-package conftest collision). Network and FFmpeg are
mocked in unit tests; live runs are `@pytest.mark.integration`.

## Dev commands
`uv sync --all-packages --dev`; `make test` / `make test-coverage` / `make lint` / `make lint-fix` /
`make type-check`. `make help` lists targets.

## Checkpoint discipline (read before implementing)
See `PROGRESS.md`. After EVERY build step: repo must be green (`uv sync`; once tests exist, `make test`
+ `make type-check` pass) and committed. One commit per step. On resume: read `PROGRESS.md`, run the
verify command, continue at the first unchecked step. Never leave a half-broken step uncommitted.

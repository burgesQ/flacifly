# flacifly — Roadmap

At-a-glance backlog. `[x]` done · `[ ]` open. IDs group by area.

## Core (C)
- [x] C1  Shared coloured logging (`ColorFormatter` / `setup_logging`) in `core`.
- [x] C2  Base `Config` dataclass + shared `types_` / `exit_codes`.
- [x] C3  SQLite layer (`db.py`): `tracks` + `review_queue` + migrations, WAL, idempotent `init_db()`.
- [x] C4  Dedup query (`track_exists`) across dirs; provenance columns.
- [x] C5  Review-queue CRUD (`enqueue_review` / `pending_reviews` / `resolve_review`).
- [x] C6  Filesystem lock-dir mutual exclusion (`locking.py`), guards overlapping runs.

## Fetcher — task 1 (F)
- [x] F1  `ytdlp_adapter`: wrap `yt_dlp.YoutubeDL`, best-audio, per-dir download-archive, cookies.
- [x] F2  Keep original best-audio file (no destructive extract).
- [x] F3  `transcode.py`: FFmpeg → FLAC, configurable compression, idempotent.
- [x] F4  `downloader.py`: read `targets.conf`, per-target subdir, record tracks, dedup.
- [x] F5  `ThreadPoolExecutor` (`--nb-worker`, default 1); per-entry error counting.
- [x] F6  `--mode {all,youtube,soundcloud,off}` (off = safe container default); `--url` one-off.
- [x] F7  `--dry-run` on all writes; `--flac-compression`, `--no-keep-original` flags.

## Tagger — task 2 (T)
- [x] T1  `identify.py`: heuristic 'Artist - Title' split + noise stripping + confidence.
- [x] T2  Resolver protocol + `HeuristicResolver` + `EmbeddedResolver`.
- [x] T3  `tags.py`: read/write FLAC Vorbis comments via mutagen (`--dry-run` aware).
- [x] T4  `tag` subcommand: auto-tag confident, queue uncertain.
- [x] T5  `review` subcommand: interactive accept/edit/skip over the queue.
- [x] T6  `dump` / `clear` subcommands.
- [ ] T7  `AcoustIDResolver` (chromaprint + MusicBrainz) via the plugin slot. *(future)*

## Container / CI / Ops (O)
- [x] O1  Dockerfile (`python:3.12-slim` + ffmpeg), non-root, volumes, safe default CMD.
- [x] O2  `ci.yml`: lint (`|| true`) + strict mypy + test + coverage.
- [x] O3  `release.yml`: buildx multi-arch (amd64 + arm64) → GHCR.
- [x] O4  `etc/systemd/flacifly.{service,timer}` oneshot + timer for the Pi.
- [x] O5  `etc/targets.conf` + `etc/ytdlp.conf` examples.

## Future / out of scope for v1 (Z)
- [ ] Z1  `dedup/`: parallel scan of legacy download dirs, group matching tracks, keep the best.
- [ ] Z2  `--watch` daemon run mode (internal scheduler) as an alternative to systemd-timer.
- [ ] Z3  Small HTTP API + front-end (browse / stream the crate). *(from sosound-tools TODOs)*
- [ ] Z4  Multi-Python CI matrix + reviewdog annotations.

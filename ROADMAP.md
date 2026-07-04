# flacifly — Roadmap

At-a-glance backlog. `[x]` done · `[ ]` open. IDs group by area.

## Core (C)
- [ ] C1  Shared coloured logging (`ColorFormatter` / `setup_logging`) in `core`.
- [ ] C2  Base `Config` dataclass + shared `types_` / `exit_codes`.
- [ ] C3  SQLite layer (`db.py`): `tracks` + `review_queue` + migrations, WAL, idempotent `init_db()`.
- [ ] C4  Dedup query (`track_exists`) across dirs; provenance columns.
- [ ] C5  Review-queue CRUD (`enqueue_review` / `pending_reviews` / `resolve_review`).
- [ ] C6  Filesystem lock-dir mutual exclusion (`locking.py`), guards overlapping runs.

## Fetcher — task 1 (F)
- [ ] F1  `ytdlp_adapter`: wrap `yt_dlp.YoutubeDL`, best-audio, per-dir download-archive, cookies.
- [ ] F2  Keep original best-audio file (no destructive extract).
- [ ] F3  `transcode.py`: FFmpeg → FLAC, configurable compression, idempotent.
- [ ] F4  `downloader.py`: read `targets.conf`, per-target subdir, record tracks, dedup.
- [ ] F5  `ThreadPoolExecutor` (`--nb-worker`, default 1); first-failure abort.
- [ ] F6  `--mode {all,youtube,soundcloud,off}` (off = safe container default); `--url` one-off.
- [ ] F7  `--dry-run` on all writes; `--flac-compression`, `--no-keep-original` flags.

## Tagger — task 2 (T)
- [ ] T1  `identify.py`: heuristic 'Artist - Title' split + noise stripping + confidence.
- [ ] T2  Resolver protocol + `HeuristicResolver` + `EmbeddedResolver`.
- [ ] T3  `tags.py`: read/write FLAC Vorbis comments via mutagen (`--dry-run` aware).
- [ ] T4  `tag` subcommand: auto-tag confident, queue uncertain.
- [ ] T5  `review` subcommand: interactive accept/edit/skip over the queue.
- [ ] T6  `dump` / `clear` subcommands.
- [ ] T7  `AcoustIDResolver` (chromaprint + MusicBrainz) via the plugin slot. *(future)*

## Container / CI / Ops (O)
- [ ] O1  Dockerfile (`python:3.12-slim` + ffmpeg), non-root, volumes, safe default CMD.
- [ ] O2  `ci.yml`: lint (`|| true`) + strict mypy + test + coverage.
- [ ] O3  `release.yml`: buildx multi-arch (amd64 + arm64) → GHCR.
- [ ] O4  `etc/systemd/flacifly.{service,timer}` oneshot + timer for the Pi.
- [ ] O5  `etc/targets.conf` + `etc/ytdlp.conf` examples.

## Future / out of scope for v1 (Z)
- [ ] Z1  `dedup/`: parallel scan of legacy download dirs, group matching tracks, keep the best.
- [ ] Z2  `--watch` daemon run mode (internal scheduler) as an alternative to systemd-timer.
- [ ] Z3  Small HTTP API + front-end (browse / stream the crate). *(from sosound-tools TODOs)*
- [ ] Z4  Multi-Python CI matrix + reviewdog annotations.

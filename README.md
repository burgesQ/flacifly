# flacifly

[![CI](https://github.com/burgesQ/flacifly/actions/workflows/ci.yml/badge.svg)](https://github.com/burgesQ/flacifly/actions/workflows/ci.yml)
[![Release](https://github.com/burgesQ/flacifly/actions/workflows/release.yml/badge.svg)](https://github.com/burgesQ/flacifly/actions/workflows/release.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![linting: ruff](https://img.shields.io/badge/linting-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![typed: mypy](https://img.shields.io/badge/typed-mypy-blue.svg)](https://mypy-lang.org/)
[![container: GHCR](https://img.shields.io/badge/ghcr.io-burgesQ%2Fflacifly-2496ED.svg)](https://github.com/burgesQ/flacifly/pkgs/container/flacifly)

Download best-quality audio from **YouTube / YouTube Music / SoundCloud**, transcode to **FLAC**, and
tag it (artist / track) — a DJ crate builder for auditioning tracks on CDJ/rekordbox before buying the
officials. Designed to run as a scheduled **oneshot container on a Raspberry Pi**.

Rewrite of the old Bash tool [`burgesQ/sosound-tools`](https://github.com/burgesQ/sosound-tools) into a
lean, tested Python project.

> ⚠️ **FLAC quality note.** YouTube/SoundCloud only serve *lossy* audio (Opus/AAC/MP3). Transcoding to
> FLAC yields a lossless *container*, not extra fidelity. flacifly keeps the original best-audio file
> next to the FLAC so nothing is lost — FLAC is produced for CDJ/rekordbox compatibility.

## Features

- 🎧 **Best-audio download** via `yt-dlp` (YouTube, YouTube Music, SoundCloud), original kept.
- 🔇 **FLAC transcode** via FFmpeg (configurable compression), idempotent.
- 🏷️ **Automatic tagging** — heuristic `Artist - Title` parsing + embedded metadata, with a pluggable
  resolver slot (AcoustID/MusicBrainz can be added later).
- 🧐 **Interactive review** — anything the tagger isn't confident about is queued in SQLite and resolved
  one-by-one with `flacifly-tag review`.
- 🚫 **No duplicates / no wasted work** — per-directory download archive + a SQLite `tracks` table dedup
  across runs and directories.
- 🐳 **Multi-arch OCI image** (`linux/amd64` + `linux/arm64`) published to GHCR — lean and Pi-friendly.
- ⏱️ **Zero idle footprint** — `Type=oneshot` systemd service + timer; nothing runs between jobs.

## Pipeline

| Task | Tool | What it does |
|------|------|--------------|
| 1 — fetch | `flacifly-fetch` | Download best audio, keep the original, transcode a FLAC copy, record in SQLite (dedup). |
| 2 — tag   | `flacifly-tag`   | Identify artist/track (heuristic + embedded metadata), write FLAC tags; low-confidence → review queue. |

## Layout

```
core/     shared: logging, SQLite (dedup + review queue), config, locking
fetcher/  task 1 — download → FLAC   (CLI: flacifly-fetch)
tagger/   task 2 — metadata + review (CLI: flacifly-tag)
etc/      targets.conf, ytdlp.conf, systemd units
dedup/    future: parallel dir comparator (scaffold only)
```

A `uv`-workspace monorepo of small `src/`-layout packages. See `CLAUDE.md` for conventions and
`ROADMAP.md` for status.

## Requirements

- **FFmpeg** on `PATH` (the FLAC transcode).
- **A JavaScript runtime — [Deno](https://deno.land) — for YouTube.** Current YouTube requires yt-dlp to
  solve a signature / *n*-challenge in JS; without a runtime it exposes only thumbnails and **every audio
  download fails** with `Requested format is not available`. Install it once:
  ```console
  $ curl -fsSL https://deno.land/install.sh | sh      # then ensure it is on PATH
  ```
  The container image already bundles Deno, so this only matters when running outside the container.
- **Cookies (optional)** for age-gated/private content must be a **Netscape-format** `cookies.txt`
  (export with a "Get cookies.txt" browser extension) — an invalid file is now rejected up front with a
  clear message instead of aborting the run.

## Usage

```console
# Task 1 — download best audio + transcode to FLAC (keeps the original)
$ flacifly-fetch --download-root ~/Music --targets etc/targets.conf --mode youtube
$ flacifly-fetch --download-root ~/Music --url "<a single URL>" --mode all   # one-off

# Task 2 — identify + write tags; uncertain tracks go to the review queue
$ flacifly-tag tag ~/Music
$ flacifly-tag review ~/Music        # walk uncertain tracks interactively
$ flacifly-tag dump ~/Music          # show current tags
```

`--mode off` (the default, and the container's default command) is a safe no-op. Add `--dry-run` to any
write command to preview without touching files. The shared SQLite DB (default
`~/.local/share/flacifly/flacifly.db`, override with `--db`) handles dedup and the review queue across
runs.

### `etc/targets.conf`

One `Name  URL` per line; the name becomes a subdirectory under `--download-root`. Lines starting with
`#` are ignored:

```
YouTube      https://www.youtube.com/playlist?list=LLxxxxxxxxxxxx
SoundCloud   https://soundcloud.com/some-artist/sets/some-set
```

> A YouTube channel **uploads** playlist (`list=UU…`) only serves 100 items via the playlist endpoint,
> so flacifly transparently rewrites it to the channel's `/videos` tab to enumerate the full catalogue.

## Run on a Raspberry Pi (container + systemd timer)

The multi-arch image is published to `ghcr.io/burgesQ/flacifly` by CI. Pull it, or build locally:

```console
$ podman pull ghcr.io/burgesq/flacifly:latest      # or: podman build -t flacifly .
$ cp etc/systemd/flacifly.{service,timer} ~/.config/systemd/user/
$ systemctl --user enable --now flacifly.timer
```

The service is `Type=oneshot` (fetch then tag, then exit) — nothing runs between scheduled runs. Edit the
unit for your host paths, target file, and schedule.

## Development

```console
$ uv sync --all-packages --dev
$ make test          # run the unit suite
$ make lint          # ruff + black + isort (read-only)
$ make type-check    # strict mypy
$ make help          # list targets
```

`uv run pytest -m integration` runs the ffmpeg/live smoke tests (the live download needs
`FLACIFLY_INTEGRATION=1`).

## License

No license yet — all rights reserved until one is added.

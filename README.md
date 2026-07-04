# flacifly

Download best-quality audio (YouTube / YouTube Music / SoundCloud), transcode to **FLAC**, and tag it
(artist / track) — a DJ crate builder for auditioning tracks on CDJ/rekordbox before buying the officials.

Rewrite of the old Bash tool [`burgesQ/sosound-tools`](https://github.com/burgesQ/sosound-tools) as a
lean Python project, designed to run as a scheduled **oneshot container on a Raspberry Pi**.

> ⚠️ **FLAC quality note.** YouTube/SoundCloud only serve *lossy* audio (Opus/AAC/MP3). Transcoding to
> FLAC yields a lossless *container*, not extra fidelity. flacifly keeps the original best-audio file
> next to the FLAC so nothing is lost. FLAC is produced for CDJ/rekordbox compatibility.

## Pipeline

| Task | Tool | What it does |
|------|------|--------------|
| 1 — fetch | `flacifly-fetch` | Download best audio (yt-dlp), keep original, transcode a FLAC copy, record in SQLite (dedup). |
| 2 — tag   | `flacifly-tag`   | Identify artist/track (heuristic + embedded metadata), write FLAC tags; low-confidence → review queue. |

Uncertain identifications persist in an intermediate SQLite DB and are resolved one-by-one with
`flacifly-tag review`.

## Layout

```
core/     shared: logging, SQLite (dedup + review queue), config, locking
fetcher/  task 1 — download → FLAC   (CLI: flacifly-fetch)
tagger/   task 2 — metadata + review (CLI: flacifly-tag)
etc/      targets.conf, ytdlp.conf, systemd units
```

## Development

```console
$ uv sync --all-packages --dev
$ make test          # run the suite
$ make lint          # ruff + black + isort (read-only)
$ make type-check    # strict mypy
$ make help          # list targets
```

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

`--mode off` (the default, and the container's default CMD) is a safe no-op. Add
`--dry-run` to any write command to preview without touching files. The shared SQLite DB
(default `~/.local/share/flacifly/flacifly.db`, override with `--db`) handles dedup and
the review queue across runs.

### On a Raspberry Pi (container + systemd timer)

```console
$ podman build -t flacifly .            # or docker; CI publishes multi-arch to GHCR
$ cp etc/systemd/flacifly.{service,timer} ~/.config/systemd/user/
$ systemctl --user enable --now flacifly.timer
```

The service is `Type=oneshot` (fetch then tag, then exit) — nothing runs between
scheduled runs. Tests: `make test` (unit); `uv run pytest -m integration` runs the
ffmpeg/live smoke tests (the live download needs `FLACIFLY_INTEGRATION=1`).

See `ROADMAP.md` for status and `CLAUDE.md` for conventions.

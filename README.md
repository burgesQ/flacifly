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

## Usage (once implemented)

```console
$ flacifly-fetch --download-root ~/Music --targets etc/targets.conf --mode youtube
$ flacifly-tag tag --path ~/Music
$ flacifly-tag review        # walk uncertain tracks interactively
```

See `ROADMAP.md` for status and `CLAUDE.md` for conventions.

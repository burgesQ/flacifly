# dedup — parallel dir comparator (future / out of scope for v1)

> Scaffold only. No implementation yet. Tracked as **Z1** in `../ROADMAP.md`.

## Problem

This isn't the first iteration of the author's music grabbing — there are ~4–5 legacy
"download dirs" scattered around, with overlapping and duplicated tracks in mixed
formats/qualities. We want to consolidate them: find the tracks that are "the same"
across dirs and keep the **best** copy.

## Intended job

1. **Scan** the configured source dirs **in parallel** (one worker per dir), collecting
   every audio file with cheap metadata (path, size, format, bitrate/sample rate, tags,
   duration).
2. **Group** likely-identical tracks. Cheap signals first (normalized `Artist - Title`,
   duration within a tolerance), optionally an acoustic fingerprint (chromaprint) for the
   uncertain ones — reusing the resolver idea from `tagger`.
3. **Rank & keep the best** per group: prefer lossless > higher bitrate > larger size,
   with format/source tie-breakers. Move/link the winner into the canonical library;
   report the losers.
4. **Uncertain matches → review.** Groups the heuristics aren't confident about are
   recorded in the shared SQLite DB (`core.db`) and resolved interactively — the same
   `review` mechanism `tagger` already uses (add a `--review` flow here or extend the
   tagger one).

## Design notes

- Will become the **4th workspace member** (`dedup/` with `src/dedup/`, console script
  e.g. `flacifly-dedup`), reusing `core` (logging, `db`, `locking`, config) exactly like
  `fetcher`/`tagger`.
- Read-only by default; every move/delete behind `--dry-run` (mandatory per `CLAUDE.md`).
- Parallel scan via `ThreadPoolExecutor` (I/O bound), `--nb-worker` like the fetcher.
- Reuse `tagger.identify` normalization for title matching; reuse the reserved
  `AcoustIDResolver` slot for fingerprint grouping.

## Not started

Nothing here is wired into the build. See the plan
(`~/.claude/plans/il-faut-que-les-harmonic-creek.md`) and `../ROADMAP.md` (Z1).

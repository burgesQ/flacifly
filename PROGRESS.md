# Build progress — flacifly

Checkpoint tracker for the incremental build (see the plan at
`~/.claude/plans/il-faut-que-les-harmonic-creek.md`). **One git commit per step.**

## Resume protocol
1. Read this file top-to-bottom.
2. Run the verify command under `## RESUME HERE`.
3. Continue at the first unchecked step. A red tree means the last step was interrupted
   mid-way — re-do only that step (`git status` shows partial work).

Green gate per step: `uv sync --all-packages --dev` resolves, and once tests exist,
`make test` + `make type-check` pass.

## Steps
- [x] 1. Skeleton + git init (workspace pyproject, pytest.ini, Makefile, targets/help.mk, package stubs). `uv sync` works.
- [x] 2. Docs: ROADMAP.md, CLAUDE.md, README.md, PROGRESS.md seeded.
- [x] 3. core base: exit_codes, logging (ColorFormatter/setup_logging), types_, config + logging tests.
- [x] 4. core.db: schema + typed CRUD + migrations + tests.
- [x] 5. core.locking: lock-dir mutual exclusion + tests.
- [x] 6. fetcher shell: ytdlp_adapter, config, exit_codes, cli skeleton, main shim + mocked tests.
- [x] 7. fetcher pipeline: transcode (FFmpeg), downloader orchestration + DB + threading + tests.
- [ ] 8. tagger identify: identify + resolvers protocol + Heuristic/Embedded + tests.
- [ ] 9. tagger tag: tags (mutagen) + tag subcommand + tests (generated FLAC).
- [ ] 10. tagger review: review interactive + review/dump/clear subcommands + tests.
- [ ] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local buildx smoke.
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 8 — tagger identify (heuristic + resolvers protocol + tests).**
Verify current state: `cd ~/repo/flacifly && make test` (should pass: 47 tests). fetcher is COMPLETE.
Now build the tagger package (task 2). Step 8 scope (no file I/O yet):
- `tagger/src/tagger/types_.py`: `Guess(artist, title, date, confidence)`, `TrackContext(raw_title,
  embedded, filepath)`.
- `tagger/src/tagger/identify.py`: normalise raw title (strip `[Official Video]`, `(HD)`, `feat.` etc.),
  split on `" - "` / `" – "` / `" — "` → (artist, title); confidence from split cleanliness + agreement
  with embedded fields (uploader/artist/track). Centralised regexes (NAMED_PATTERNS style).
- `tagger/src/tagger/resolvers/__init__.py`: `Resolver` Protocol (`resolve(ctx) -> Guess | None`);
  `HeuristicResolver`, `EmbeddedResolver`. (AcoustID slot reserved — no dep.)
- `tagger/src/tagger/config.py`: `TagConfig(BaseConfig)` with `path`, `confidence_threshold=0.8`.
- `tagger/src/tagger/exit_codes.py` (re-export core; add TAG_ERROR if needed).
Tests: `tagger/tests/test_identify.py` (splits, noise stripping, confidence ordering, resolver combine).
Then step 9 adds `tags.py` (mutagen) + `tag` subcommand; step 10 adds `review` interactive + subcommands.
The `embedded_json` written by fetcher (keys: title, uploader, artist, track, album, release_year,
upload_date) is the EmbeddedResolver's input. Read a track's embedded_json from `core.db` in step 9.

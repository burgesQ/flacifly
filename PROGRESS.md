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
- [x] 8. tagger identify: identify + resolvers protocol + Heuristic/Embedded + tests.
- [ ] 9. tagger tag: tags (mutagen) + tag subcommand + tests (generated FLAC).
- [ ] 10. tagger review: review interactive + review/dump/clear subcommands + tests.
- [ ] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local buildx smoke.
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 9 — tagger tags (mutagen) + `tag` subcommand.**
Verify current state: `cd ~/repo/flacifly && make test` (should pass: 67 tests).
Build:
- `tagger/src/tagger/tags.py`: `read_tags(flac_path) -> dict`, `write_tags(flac_path, artist, title,
  date=None, dry_run=False)` via `mutagen.flac.FLAC` (Vorbis comments ARTIST/TITLE/DATE/ALBUM/GENRE);
  low-level I/O only. mutagen import may need lazy import; mypy override already set.
- `tagger/src/tagger/tagging.py` (or in cli): the `tag` operation — iterate the FLAC files under
  `cfg.path`, for each find its DB track (by flac_path) to get embedded_json + raw_title, build
  TrackContext, `best_guess`; if `confidence >= cfg.confidence_threshold` write tags + set status TAGGED;
  else `db.enqueue_review`. `--dry-run` aware.
- `tagger/src/tagger/cli.py` (subcommand style like manga editor): subparsers tag/review/dump/clear;
  `_add_logging_args`; `main.py` shim. Step 9 implements `tag` + `dump`; step 10 implements `review` +
  `clear` and interactive flow.
Tests: `tagger/tests/test_tags.py` using a REAL generated FLAC fixture (mutagen can create one: write a
minimal FLAC — see conftest factory `make_flac`). Assert write→read round-trip, dry-run no-op.
NOTE: to match a FLAC file to its DB row, fetcher stored `flac_path`. Add `core.db.get_track_by_flac_path`
(new helper) OR query in tagger. Prefer adding the helper to core.db for reuse. embedded_json is JSON in
the `tracks` row; parse with json.loads for the EmbeddedResolver.

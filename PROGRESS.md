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
- [x] 9. tagger tag: tags (mutagen) + tag subcommand + tests (generated FLAC).
- [ ] 10. tagger review: review interactive + review/dump/clear subcommands + tests.
- [ ] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local buildx smoke.
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 10 — tagger review (interactive) + `review`/`clear` subcommands.**
Verify current state: `cd ~/repo/flacifly && make test` (should pass: 80 tests).
IMPORTANT pytest gotcha (already handled): test module basenames must be UNIQUE across packages
(no __init__.py in tests dirs, default prepend import mode). We renamed to test_fetch_cli.py /
test_tag_cli.py. Do NOT add a plain `test_cli.py` — and importlib mode is NOT usable (the repo-level
`tagger/` dir shadows the installed package).
Build step 10:
- `tagger/src/tagger/review.py`: `review_pending(cfg, prompt=input, out=print) -> int`. Loop
  `db.pending_reviews`; for each, join its track (`db.get_track`) to get the FLAC path + raw_title;
  show raw vs guessed artist/title; prompt accept (Enter/y) / edit (type new "Artist - Title") / skip (s).
  On accept/edit: `tags.write_tags` + `db.resolve_review(decision=...)` + `db.set_status(TAGGED)`.
  On skip: `db.resolve_review(decision=SKIPPED)`. `prompt`/`out` injected for testing (feed a list of
  inputs). Honour `cfg.dry_run`.
- `tagger/src/tagger/tagging.py`: add `clear_directory(cfg)` — remove managed tags (mutagen delete).
  Add `tags.clear_tags(flac, dry_run)`.
- `tagger/src/tagger/cli.py`: add `review` subparser (path optional? uses --db + path for FLAC root) and
  `clear` subparser (path + --dry-run). Wire into main().
Tests: `tagger/tests/test_review.py` (feed prompt inputs: accept/edit/skip → assert tags written +
review resolved + status). Extend test_tag_cli for review/clear dispatch.
Then: step 11 configs+Dockerfile, step 12 CI, step 13 integration/polish, step 14 dedup scaffold.

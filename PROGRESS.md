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
- [ ] 5. core.locking: lock-dir mutual exclusion + tests.
- [ ] 6. fetcher shell: ytdlp_adapter, config, exit_codes, cli skeleton, main shim + mocked tests.
- [ ] 7. fetcher pipeline: transcode (FFmpeg), downloader orchestration + DB + threading + tests.
- [ ] 8. tagger identify: identify + resolvers protocol + Heuristic/Embedded + tests.
- [ ] 9. tagger tag: tags (mutagen) + tag subcommand + tests (generated FLAC).
- [ ] 10. tagger review: review interactive + review/dump/clear subcommands + tests.
- [ ] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local buildx smoke.
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 5 — core.locking (filesystem lock-dir mutual exclusion + tests).**
Verify current state: `cd ~/repo/flacifly && make test` (should pass: 16 tests, core logging + db).
Add `core/src/core/locking.py`: a context manager acquiring a lock dir (e.g. `mkdir` atomicity) named
per job (`fetch`/`tag`), raising a `LockError` if already held; releases on exit; stale-lock handling
optional. Exit code `LOCKED = 5` already in `core.exit_codes`. Port intent from sosound-tools lock dirs.
Add `core/tests/test_locking.py` (acquire/release, double-acquire raises, cleanup on exception).

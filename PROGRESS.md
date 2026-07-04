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
- [x] 10. tagger review: review interactive + review/dump/clear subcommands + tests.
- [x] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local podman build smoke.
- [x] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [x] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 14 — dedup/ scaffold (FINAL step).**
Verify current state: `cd ~/repo/flacifly && make test` (89 passed, 1 skipped — the live fetch is
gated by FLACIFLY_INTEGRATION=1; the real-ffmpeg transcode test runs when ffmpeg is present).
Build step 14 (docs-only scaffold, no code, no new tests):
- `dedup/README.md`: spec for the future parallel dir-comparator (out of scope for v1). Describe the job:
  scan the user's ~4-5 legacy download dirs in parallel, group matching tracks (normalized title /
  fingerprint), keep the "best" (bitrate/format/size), record uncertain matches in `core.db` for
  `flacifly-tag review`. Reference ROADMAP Z1. Note it will become a 4th workspace member later.
After step 14: project COMPLETE. Optionally run full `make lint && make type-check && make test` and do a
final `podman build` smoke. All 14 build steps done.

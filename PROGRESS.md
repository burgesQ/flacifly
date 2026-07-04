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
- [x] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## DONE — all 14 build steps complete ✅
v1 is fully built and green: `make test` → 89 passed, 1 skipped; `make lint` + `make type-check` clean;
`podman build` succeeds and the container runs (safe no-op default + working CLIs).

Remaining open items (deliberately deferred, tracked in ROADMAP):
- T7 AcoustID/MusicBrainz resolver (reserved plugin slot).
- Z1 dedup/ dir-comparator (scaffolded in dedup/README.md).
- Z2 --watch daemon mode; Z3 HTTP API/front-end; Z4 CI matrix + reviewdog.
- arm64 image is verified in CI (release.yml) on first push to main / a `v*` tag; locally only
  podman/amd64 was smoke-tested (docker + QEMU not installed in the dev env).

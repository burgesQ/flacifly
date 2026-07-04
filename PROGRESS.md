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
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 13 — integration tests + polish.**
Verify current state: `cd ~/repo/flacifly && make test` (88 tests) + `uv sync --locked` OK.
Build step 13:
- Add a few `@pytest.mark.integration` tests (opt-in; excluded from default run via `-m "not
  integration"`? currently they'd run — guard them so they SKIP without network/ffmpeg, or mark and let
  CI skip). Suggested: a fetch smoke that, IF network+ffmpeg available, downloads one very short public
  YouTube URL to a tmp dir and asserts a FLAC + original exist + DB row. Use pytest.importorskip / a
  shutil.which('ffmpeg') skip guard so it never fails in CI without ffmpeg.
- Consider adding `-m "not integration"` note to README / Makefile `test` (keep default `make test` fast).
- Finalize README usage section (already drafted) — verify the example commands match the real CLI flags.
Then step 14: `dedup/README.md` scaffold (future dir-comparator spec) — the last step.
NOTE (arm64): multi-arch build is verified in CI (release.yml) on first push to main / tag; locally only
podman/amd64 was smoke-tested (docker+QEMU not installed here).

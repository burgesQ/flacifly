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
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 12 — CI (.github/workflows/ci.yml + release.yml multi-arch → GHCR).**
Verify current state: `cd ~/repo/flacifly && make test` (88 tests). Container: `podman build -t
flacifly:test .` succeeds (docker is NOT installed here — use podman locally; CI uses docker).
Build step 12:
- `.github/workflows/ci.yml`: adapt manga_manager's (astral-sh/setup-uv@v7 pinned 0.9.23,
  actions/checkout@v6). lint job: ruff/black/isort with `|| true`, then strict
  `uv run mypy -p core -p fetcher -p tagger` (can fail). test job: `uv sync --locked --all-packages
  --dev` then `uv run pytest --cov=core --cov=fetcher --cov=tagger --cov-report=html . -q`, upload
  htmlcov. NOTE: `uv.lock` must be committed for `--locked` (run `uv lock` and commit it — check it isn't
  gitignored; .gitignore currently ignores *.db but NOT uv.lock, good).
- `.github/workflows/release.yml`: docker/setup-qemu-action + docker/setup-buildx-action +
  docker/login-action (GHCR, `${{ github.actor }}` / `secrets.GITHUB_TOKEN`) +
  docker/build-push-action with `platforms: linux/amd64,linux/arm64`, push to
  `ghcr.io/burgesq/flacifly`, tags on git tags + `latest` on main. `permissions: packages: write`.
Then step 13 integration/polish (@pytest.mark.integration live smoke, finalize README), step 14
dedup/README.md scaffold.
KNOWN: `docker buildx build --platform linux/amd64,linux/arm64 .` (plan verification) needs docker+QEMU;
locally only podman/amd64 was smoke-tested — arm64 is verified in CI on first tag push.

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
- [ ] 11. Configs + container: etc/ configs, systemd units, Dockerfile + local buildx smoke.
- [ ] 12. CI: ci.yml + release.yml (multi-arch GHCR).
- [ ] 13. Integration + polish: @pytest.mark.integration smoke tests, finalize README.
- [ ] 14. Scaffold: dedup/README.md (future dir-comparator spec).

## RESUME HERE
**Next: step 11 — configs + container (etc/ files, systemd units, Dockerfile).**
Verify current state: `cd ~/repo/flacifly && make test` (should pass: 88 tests). BOTH packages COMPLETE.
pytest gotcha (handled): unique test basenames, default prepend import mode (importlib mode breaks —
repo-level `tagger/` dir shadows the installed package). Don't reintroduce `test_cli.py`.
Build step 11:
- `etc/targets.conf` (example `Name  URL` lines, mostly commented; port a couple from sosound-tools
  dl.conf: a YouTube playlist + a SoundCloud URL, commented).
- `etc/ytdlp.conf` (documented example of yt-dlp options — informational; the adapter builds opts in code,
  but ship this as reference / for `--ytdlp-conf`).
- `etc/systemd/flacifly.service` (Type=oneshot; ExecStart runs `docker run --rm ... flacifly-fetch ...`
  then a second ExecStart for `flacifly-tag tag`) and `etc/systemd/flacifly.timer` (OnCalendar=daily,
  Persistent=true, WantedBy=timers.target). Use %h or a documented path for volumes.
- `Dockerfile`: `python:3.12-slim`, `apt-get install --no-install-recommends ffmpeg ca-certificates`,
  copy repo, `pip install ./core ./fetcher ./tagger` (or `pip install .` won't work — root has no
  package; install the three members). Non-root user, VOLUME for music + db + config, default
  `CMD ["flacifly-fetch","--mode","off","--download-root","/music"]` (safe no-op).
- `.dockerignore` already exists.
Verify: `docker buildx build --platform linux/amd64 -t flacifly:test .` (buildx allowed per plan).
No new tests strictly required; a build smoke is the gate. Then step 12 CI, 13 integration/polish, 14
dedup scaffold.

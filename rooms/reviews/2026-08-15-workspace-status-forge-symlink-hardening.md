# Sprint Tick Review: workspace status symlink hardening

- **Selected slice:** Make `workspace_status()` refuse symlinked `.forge` directories without following them, including under replacement races.
- **Changed files:** `src/forgecode_agent/cli.py`, `tests/unit/test_cli_status.py`.
- **Implementation:** Reused descriptor-relative `O_NOFOLLOW` traversal for `.forge/config.toml` and `.forge/active-task.toml`, validating regular files before parsing. Existing regular-directory status behavior remains unchanged.
- **TDD evidence:** Added a regression test first. RED failed because a symlinked `.forge` exposed the target config; the minimal implementation then produced GREEN. The regression also proves target active-task metadata is not read.
- **Verification:** Focused status tests: **10 passed**. Full suite: **326 passed**. `python -m compileall -q src tests`: passed. `git diff --check`: passed. Static security scan: no findings. Independent spec review: PASS. Independent quality/security review: APPROVED after descriptor-based race hardening.
- **Build:** Wheel build not attempted because the environment lacks the `build` module (existing environment limitation).
- **Status:** Ready for orchestrator commit and push. No secrets, network calls, or unrelated files included.

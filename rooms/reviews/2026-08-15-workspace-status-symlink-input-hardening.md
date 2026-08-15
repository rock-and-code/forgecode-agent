# Sprint Tick Review: workspace status symlink-input hardening

- **Selected slice:** Make `workspace_status()` classify a symlink supplied as the workspace path as missing, without following or exposing target metadata.
- **Changed files:** `src/forgecode_agent/cli.py`, `tests/unit/test_cli_status.py`.
- **Implementation:** Added an explicit `Path.is_symlink()` guard before workspace validity classification. Existing descriptor-relative `O_NOFOLLOW` reads continue to prevent config or active-task traversal through symlinked paths; regular directories and `.forge` symlink handling are unchanged.
- **TDD evidence:** Added a focused regression test first. RED showed `workspace_state="ok"` for a symlink input; the minimal guard produced GREEN. Focused status tests: **11 passed**. Full suite: **327 passed**.
- **Verification:** `python -m compileall -q src tests` passed; `git diff --check` passed; static security scan found no findings. Spec review: PASS. Independent quality/security review: APPROVED with no blocking issues.
- **Build/lint:** `python -m build` unavailable because the environment lacks the `build` module. Ruff reports two pre-existing unused-variable findings outside this slice (`src/forgecode_agent/cli.py:517` and `tests/unit/test_cli_init.py:207`); no new lint findings were introduced.
- **Status:** Ready for orchestrator commit and push. No secrets, network calls, destructive commands, or unrelated source changes included.

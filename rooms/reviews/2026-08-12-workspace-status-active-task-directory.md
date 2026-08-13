# Sprint Tick Review: workspace status active-task directory hardening

## Selected slice

Harden `workspace_status()` so a non-file `.forge/active-task.toml` path, specifically a directory, is ignored safely instead of being passed to the TOML reader. The status result must remain usable with `active_task=None`.

## Changed files

- `src/forgecode_agent/cli.py` — use `Path.is_file()` before reading the active-task file.
- `tests/unit/test_cli_status.py` — add a regression test proving a directory is not parsed and produces no active task.
- `rooms/reviews/2026-08-12-workspace-status-active-task-directory.md` — record sprint evidence.

## TDD evidence

- RED: focused test failed before implementation because `workspace_status()` attempted to read the directory; the test raised `AssertionError: should not read directory`.
- GREEN: focused regression test passed after the minimal `is_file()` guard.

## Review and verification

- Spec-compliance review: PASS.
- Independent quality/security review: APPROVED; no critical, important, or minor issues.
- Focused test: `python -m pytest -q tests/unit/test_cli_status.py::test_workspace_status_ignores_active_task_directory` — passed.
- Full suite: `python -m pytest -q` — passed (`307 passed`).
- `git diff --check` — passed.
- Added-line security scan — no findings.
- Packaging check: `python -m pip wheel . --no-deps -w /tmp/forgecode-workspace-status-wheel-check` — passed.
- Independent pre-commit security/logic review: PASS; no security concerns or blocking logic errors.

## Scope and status

No unrelated changes, secrets, or external side effects were involved. Ready for orchestrator-owned commit and push.

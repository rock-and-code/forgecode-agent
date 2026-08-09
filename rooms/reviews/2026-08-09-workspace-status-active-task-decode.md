# Sprint Tick Review: workspace status active-task decode hardening

## Selected slice

Harden `workspace_status()` so a malformed/unreadable `.forge/active-task.toml` does not crash CLI status reporting.

## Files changed

- `src/forgecode_agent/cli.py` — treats `OSError`/`UnicodeDecodeError` while reading active-task metadata as no active task.
- `tests/unit/test_cli_status.py` — adds invalid UTF-8 active-task regression coverage.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_cli_status.py::test_workspace_status_ignores_active_task_decode_error` failed before implementation with `UnicodeDecodeError` from `_read_simple_toml_strings(active_task_file)`.
- GREEN: focused test passed after the minimal handler change.
- Relevant suite: `python -m pytest -q tests/unit/test_cli_status.py` passed (`7 passed`).

## Verification

- `python -m pytest -q` passed (`94 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.
- Static scan of added lines found no hardcoded secrets, shell injection, eval/exec, pickle, or SQL string-formatting patterns.

## Review

- Spec compliance review: PASS.
- Quality review: APPROVED; noted optional future OSError-specific coverage.
- Independent final review: PASS.

## Next recommended slice

Add another narrow CLI status hardening case for `.forge/active-task.toml` as a directory/unreadable path, or continue CLI status/doctor polish around malformed config handling symmetry.

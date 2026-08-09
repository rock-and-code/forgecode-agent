# Sprint Tick Review: workspace status config decode hardening

## Selected slice

Harden `workspace_status()` so a malformed/unreadable `.forge/config.toml` does not crash CLI status reporting.

## Files changed

- `src/forgecode_agent/cli.py` — catches `OSError`/`UnicodeDecodeError` while reading status config metadata and treats provider as unset.
- `tests/unit/test_cli_status.py` — adds invalid UTF-8 config regression coverage.

## TDD evidence

- RED: `pytest tests/unit/test_cli_status.py::test_workspace_status_ignores_invalid_utf8_config` failed before implementation with `UnicodeDecodeError` from `_read_simple_toml_strings(config_file)`.
- GREEN: the same focused test passed after the minimal handler change.
- Relevant suite: `pytest tests/unit/test_cli_status.py` passed (`8 passed`).

## Verification

- Full test suite: `python -m pytest -q` passed (`95 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.

## Independent review

- Spec compliance review: PASS.
- Code quality review: APPROVED; no critical, important, or minor issues.

## Notes

`config_state` intentionally remains `ok` for a malformed config that exists as a file, while `model_provider` falls back to `None`, matching the bounded status-reporting behavior used for malformed active-task metadata.

## Next recommended slice

Add another narrow CLI status/doctor polish case for unreadable/malformed active-task paths or move to golden transcript test infrastructure.

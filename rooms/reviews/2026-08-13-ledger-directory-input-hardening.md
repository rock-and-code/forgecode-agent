# Sprint review: ledger directory-input hardening

## Selected slice

Harden `RunLedger.read_jsonl()` so a directory or other unreadable/non-regular input path produces a privacy-safe `ValueError` instead of leaking a raw filesystem exception.

## Changed files

- `src/forgecode_agent/ledger.py` — normalize `OSError` from the input read to `ValueError("Cannot read JSONL ledger file/path")`, suppressing underlying path details.
- `tests/unit/test_run_ledger.py` — add a regression test for directory input.

## TDD evidence

- RED: `pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_directory_input_with_value_error` failed as expected with `IsADirectoryError` before the implementation change.
- GREEN: focused regression test passed after the minimal `OSError` normalization.

## Review and verification

- Spec-compliance review: PASS.
- Independent quality/security review: APPROVED; no critical or important issues.
- Focused test: passed (`1 passed`).
- Full suite: `python -m pytest -q` — passed (`311 passed`).
- Packaging: `python -m pip wheel . --no-deps -w /tmp/forgecode-ledger-wheel-check` — passed; wheel built successfully.
- `git diff --check` — passed.
- No secrets, unrelated changes, or external user-facing actions were involved.

## Status

Ready for orchestrator-owned local commit and normal push to `origin/main`.

# Sprint Tick Review: audit CLI symlink-loop parent golden transcript

Date: 2026-08-22

## Selected slice

Add deterministic golden-transcript coverage for the existing `forgecode audit` symlink-loop parent error path. The focused test verifies exit code 1, exact stable output, and that no traceback or unrelated path data is disclosed.

## Changed files

- `tests/unit/test_cli_audit.py` — isolates the loop under a relative working directory, normalizes only the platform-dependent errno number, and compares the existing error branch with a golden fixture.
- `tests/golden/audit_symlink_loop_parent.txt` — expected stable error transcript.
- `rooms/reviews/2026-08-22-audit-symlink-loop-golden-transcript.md` — sprint evidence.

## TDD evidence

- RED: focused test failed with `FileNotFoundError` because `tests/golden/audit_symlink_loop_parent.txt` was absent.
- GREEN: focused test passed after adding the minimal fixture (`1 passed`).

## Independent review

- Spec compliance: PASS.
- Code quality/security review: APPROVED; only non-blocking portability/maintainability observations for this intentionally POSIX symlink case.
- Pre-commit security/logic review: PASS; no security concerns or logic errors.

## Verification

- Focused test: `python -m pytest -q tests/unit/test_cli_audit.py::test_audit_reports_symlink_loop_parent_as_golden_error_transcript_without_traceback` — **1 passed**.
- Full suite: `python -m pytest --tb=no -q` — **358 passed**.
- Ruff: `python -m ruff check tests/unit/test_cli_audit.py` — passed.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` — passed.
- Added-line security scan — no findings.

Status: ready to commit and push.

# Review: invalid audit limit golden transcript

- **Date:** 2026-08-22
- **Selected slice:** Add deterministic golden-transcript coverage for `forgecode audit --limit 0`, which the existing `_positive_limit` argparse validator rejects.
- **Changed files:**
  - `tests/unit/test_cli_audit.py` — added a focused test asserting exit code `2` and matching the combined argparse stderr transcript against a fixture.
  - `tests/golden/audit_limit_zero_invalid.txt` — added the expected deterministic two-pass argparse error transcript.
  - `rooms/reviews/2026-08-22-audit-invalid-limit-golden-transcript.md` — this review artifact.
- **Production code:** unchanged.

## TDD evidence

- **RED:** Before adding the fixture, the focused test failed with `FileNotFoundError` for `tests/golden/audit_limit_zero_invalid.txt`.
- **GREEN:** After adding the fixture:
  - `pytest -q tests/unit/test_cli_audit.py::test_audit_rejects_zero_limit_as_golden_error_transcript` — **1 passed**.

## Verification

- `pytest -q` — **361 passed in 0.24s**.
- `git diff --check` — passed with no output.
- The captured transcript is deterministic: argparse emits the same validation error twice because `main()` performs a preliminary parse and `_main_impl()` parses again; the fixture records both messages.

## Review status

Slice complete and review-ready. No unrelated edits, secrets, commit, or push.

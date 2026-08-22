# Review: non-integer audit limit golden transcript

- **Date:** 2026-08-22
- **Selected slice:** Add deterministic golden-transcript coverage for `forgecode audit --limit not-an-integer`.
- **Changed files:**
  - `tests/unit/test_cli_audit.py` — focused test asserting exit code `2` and exact combined argparse output.
  - `tests/golden/audit_limit_non_integer_invalid.txt` — expected deterministic two-pass argparse error transcript.
  - this review artifact.
- **Production code:** unchanged.

## TDD evidence

- **RED:** Focused test initially failed because `tests/golden/audit_limit_non_integer_invalid.txt` did not exist.
- **GREEN:** Focused test passed after adding the fixture.

## Verification

- `python -m pytest -q tests/unit/test_cli_audit.py::test_audit_rejects_non_integer_limit_as_golden_error_transcript` — **1 passed**.
- `python -m pytest -q` — **362 passed**.
- `git diff --check` — passed.
- Spec review — **PASS**.
- Quality review — **APPROVED**; no critical or important issues.

The fixture records argparse's duplicate diagnostic because `main()` performs a preliminary parse before `_main_impl()` parses again. No secrets, production changes, or unrelated files are included.

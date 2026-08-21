# Sprint Tick Review: audit CLI missing-log golden transcript

Date: 2026-08-22

## Selected slice

Add deterministic golden-transcript coverage for the existing `forgecode audit` CLI missing-log error path. The focused test verifies exit code 1, exact stable output, and that the requested missing path is not created.

## Changed files

- `tests/unit/test_cli_audit.py` — replaces the inline missing-log output assertion with a focused golden-transcript assertion using a stable relative path.
- `tests/golden/audit_missing_log.txt` — expected missing-log error transcript.
- `rooms/reviews/2026-08-22-audit-missing-log-golden-transcript.md` — this progress artifact.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_cli_audit.py::test_audit_reports_missing_log_as_golden_error_transcript_without_creating_it` failed because `tests/golden/audit_missing_log.txt` was absent (`1 failed`).
- GREEN: the same focused test passed after adding the minimal fixture (`1 passed`).

## Verification

- Full suite: `python -m pytest -q` — **358 passed**.
- No production files changed.
- No commit or push performed.

## Concerns

None. The relative `missing.jsonl` argument keeps the golden output stable while `tmp_path` plus `monkeypatch.chdir` isolates the non-creation assertion.

Status: ready for integration review.

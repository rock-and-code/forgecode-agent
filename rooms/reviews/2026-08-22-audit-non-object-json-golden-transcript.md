# Sprint Tick Review: audit CLI non-object JSON golden transcript

Date: 2026-08-22

## Selected slice

Add deterministic golden-transcript coverage for the existing `forgecode audit --limit N` error path when a JSONL row parses successfully but is not an object. The focused test covers representative array and string rows, verifying exit code 1, the stable line-numbered error, no traceback, and no disclosure of unrelated payload data.

## Changed files

- `tests/unit/test_cli_audit.py` — adds the focused non-object JSON golden assertion for array and string rows.
- `tests/golden/audit_non_object_json.txt` — expected error transcript.
- `rooms/reviews/2026-08-22-audit-non-object-json-golden-transcript.md` — this artifact.

No production code was changed.

## TDD evidence

- RED: `pytest -q tests/unit/test_cli_audit.py::test_audit_reports_non_object_json_as_golden_error_transcript_without_traceback` failed because the golden fixture was absent (`FileNotFoundError`). A separate string-specific RED was not practical: the existing generic non-object error path and shared stable transcript are expected to handle the added representative input without production changes.
- GREEN: after adding the minimal fixture and parameterizing the focused assertion for array and string rows, focused audit tests passed (`2 passed`; 11 audit-file tests total).

## Verification

- Focused test: `pytest -q tests/unit/test_cli_audit.py::test_audit_reports_non_object_json_as_golden_error_transcript_without_traceback` — **2 passed**.
- Full suite: `pytest -q` — **360 passed**.
- `git diff --check` — passed.

Status: ready for orchestrator review and commit; no commit or push performed.

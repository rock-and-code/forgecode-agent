# Sprint Tick Review: audit CLI final JSONL event without newline

Date: 2026-08-23

## Selected slice

Add deterministic golden-transcript coverage for `forgecode audit` reading valid JSONL when the final event has no trailing newline. The test uses a regular audit log, limits output to two events, and verifies the exact sorted JSONL transcript.

## Changed files

- `tests/unit/test_cli_audit.py` — focused regression test creating a valid two-event log whose final line has no newline.
- `tests/golden/audit_final_event_no_newline.jsonl` — deterministic expected transcript with no secrets.
- `rooms/reviews/2026-08-23-audit-final-event-no-newline-golden-transcript.md` — this review artifact.

No production code changed; no commit was created.

## TDD evidence

- RED: focused test failed because `tests/golden/audit_final_event_no_newline.jsonl` was absent.
- GREEN: focused test passed after adding the minimal golden fixture.

## Verification

- Focused test: `pytest -q tests/unit/test_cli_audit.py::test_audit_reads_valid_final_event_without_trailing_newline_as_golden_transcript` — passed (`1 passed`).
- Audit test module: `pytest -q tests/unit/test_cli_audit.py` — passed (`16 passed`).
- Full test suite: `pytest --tb=no -q` — passed (`365 passed`).
- `git diff --check` — passed.

Status: verified and ready for parent review/commit.

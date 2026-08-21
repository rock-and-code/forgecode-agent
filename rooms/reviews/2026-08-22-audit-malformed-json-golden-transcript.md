# Sprint Tick Review: audit CLI malformed-JSON golden transcript

Date: 2026-08-22

## Selected slice

Add deterministic golden-transcript coverage for the existing `forgecode audit --limit N` CLI error path when the audit JSONL contains malformed JSON. The test verifies line-numbered failure, stable output, exit status, and that malformed contents are not disclosed.

## Changed files

- `tests/unit/test_cli_audit.py` — adds focused malformed-JSON CLI golden assertion.
- `tests/golden/audit_malformed_json.txt` — expected error transcript.
- `rooms/reviews/2026-08-22-audit-malformed-json-golden-transcript.md` — this artifact.

## TDD evidence

- RED: focused test failed because the new golden fixture was absent.
- GREEN: focused audit tests passed (`9 passed`).

## Independent review

- Spec compliance: PASS.
- Code quality/security review: APPROVED; no critical or important issues.
- Final integration review: APPROVED; intended paths only, no generated artifacts or unrelated changes.

## Verification

- Full suite: `python -m pytest --tb=no -q` — **358 passed**.
- Ruff: passed for modified Python test file.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` — passed.
- Added-line security scan: no findings expected; changes are test/fixture only.

Status: ready for final integration review, commit, and push.

# Sprint Tick Review: audit CLI symlink-log golden transcript

Date: 2026-08-21

## Selected slice

Add deterministic golden-transcript coverage for the existing `forgecode audit` symlink-log rejection path. The focused test uses stable relative paths, normalizes only the platform-dependent errno number to a stable placeholder before exact comparison, and retains the secret non-disclosure assertion.

## Changed files

- `tests/unit/test_cli_audit.py` — extends the existing symlink rejection test with a narrowly scoped errno-number normalization, golden transcript comparison, and isolated relative-path setup.
- `tests/golden/audit_symlink_log.txt` — expected symlink rejection transcript with a platform-stable errno placeholder.
- `rooms/reviews/2026-08-21-audit-symlink-log-golden-transcript.md` — this review artifact.

## TDD evidence

- RED: focused test failed before the fixture existed with `FileNotFoundError` for `tests/golden/audit_symlink_log.txt` (`1 failed`).
- GREEN: `python -m pytest -q tests/unit/test_cli_audit.py::test_audit_rejects_symlink_log_as_golden_error_transcript` — `1 passed`.

## Verification

- Full suite: `python -m pytest -q` — **358 passed**.
- Ruff: `python -m ruff check tests/unit/test_cli_audit.py` — passed.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-symlink-golden-wheel-check` — succeeded.
- `git diff --check` — passed.
- No production code changed; no commit or push performed.

## Concerns

None. The relative `audit.jsonl` argument makes the transcript deterministic, and only the numeric errno component is normalized; the rejection wording, path, exit status, and secret non-disclosure coverage remain exact.

Status: ready for integration review.

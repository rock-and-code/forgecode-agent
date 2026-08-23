# Sprint Tick Review: audit CLI FIFO golden transcript

Date: 2026-08-23

## Selected slice

Add deterministic golden-transcript coverage for `forgecode audit` when `--audit-log` points to an existing FIFO. The command must reject the non-regular file promptly without blocking, leaking the path, or changing production behavior.

## Changed files

- `tests/unit/test_cli_audit.py` — subprocess-based FIFO rejection test with bounded timeout, exact golden output, portability skips, and inherited environment preservation.
- `tests/golden/audit_fifo_log.txt` — expected stable rejection transcript.
- `rooms/reviews/2026-08-23-audit-fifo-golden-transcript.md` — this artifact.

No production code changed; no secrets or external side effects.

## TDD evidence

- RED: focused test failed because `tests/golden/audit_fifo_log.txt` was absent.
- GREEN: focused FIFO test passed after adding the minimal fixture; audit test module passed (`15 passed`).
- Quality revision: increased timeout to 5 seconds, made only recognized unsupported-FIFO errors skippable, and preserved the subprocess environment.

## Independent review

- Spec compliance: PASS.
- Code quality/security review: APPROVED after revision; no critical or important issues remain. One redundant non-blocking assertion was noted.

## Verification

- Focused FIFO test: `python -m pytest -q tests/unit/test_cli_audit.py::test_audit_rejects_fifo_without_blocking_as_golden_error_transcript` — passed.
- Full pytest: `python -m pytest --tb=no -q` — `364 passed`.
- Ruff: `python -m ruff check tests/unit/test_cli_audit.py` — passed.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` — passed.
- Added-line security scan — no findings.

Status: verified and ready for commit/push.

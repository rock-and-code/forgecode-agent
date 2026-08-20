# Sprint Tick Review: durable audit-event appends

Date: 2026-08-20

## Selected slice

Harden CLI JSONL audit-event writes so a successful append flushes buffered text and calls `fsync` on the regular audit descriptor before returning. Preserve JSONL format, append behavior, symlink defenses, and command-result semantics.

## Changed files

- `src/forgecode_agent/cli.py` — flushes and fsyncs each audit event after writing.
- `tests/unit/test_cli_audit_logging.py` — regression coverage verifies fsync receives a live descriptor and the event is persisted.
- `rooms/reviews/2026-08-20-audit-event-fsync.md` — this artifact.

## TDD evidence

- RED: focused regression test failed because no fsync call occurred (`0 == 1`).
- GREEN: focused test passed after the minimal flush/fsync implementation.

## Independent review

- Spec compliance: PASS.
- Code quality/security review: APPROVED.
- Final integration review: APPROVED; no unrelated files or blockers.

## Verification

- Full suite: `python -m pytest --tb=no -q` — **357 passed**.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` — passed.
- Modified-file Ruff: only the documented pre-existing `F841` at `src/forgecode_agent/cli.py:519`; no new lint issue.
- Added-line security scan: no findings.

Status: ready to commit and push.

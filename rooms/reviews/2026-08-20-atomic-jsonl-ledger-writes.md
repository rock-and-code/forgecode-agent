# Sprint Tick Review: atomic JSONL ledger writes

Date: 2026-08-20

## Selected slice

Harden `RunLedger.write_jsonl` so serialization and filesystem failures cannot leave a truncated or partial ledger. Existing destination contents and restrictive permissions must remain safe, while preserving descriptor-relative symlink defenses and existing error contracts.

## Changed files

- `src/forgecode_agent/ledger.py` — pre-serializes rows, writes through a secure random exclusive temporary file, preserves existing mode bits with `fchmod`, atomically replaces the destination, and normalizes unsupported descriptor-relative replacement errors.
- `tests/unit/test_run_ledger.py` — regression coverage for serialization-failure preservation/cleanup, secure temporary handling, mode preservation under umask, and replacement capability errors.
- `rooms/reviews/2026-08-20-atomic-jsonl-ledger-writes.md` — this artifact.

## TDD evidence

- RED: focused regression test failed because the prior implementation truncated the existing destination on a later serialization failure.
- GREEN: focused and ledger test suites passed after the minimal implementation.
- Revision RED/GREEN: permission-preservation and replacement-error tests were added before their corresponding fixes; all passed after revision.

## Independent review

- Spec compliance: PASS after permission-bit preservation fix.
- Code quality/security review: APPROVED; no critical, important, or minor issues.

## Verification

- Full suite: `python -m pytest --tb=no -q` — **356 passed**.
- Ledger tests: **48 passed**.
- Ruff on modified files: passed.
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` — passed.
- Added-line security scan: no hardcoded-secret, shell-injection, eval/exec, pickle, or SQL-injection findings.

Status: ready to commit and push.

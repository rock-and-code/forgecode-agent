# Structured CLI Logging Sprint Review

## Selected slice

B5: Add structured logging. Acceptance: log command, timestamp, action type, and outcome.

## Implementation

Added opt-in `--audit-log PATH` / `--audit-log=PATH` support for `doctor`, `status`, `init`, and `config`. Each invocation appends one JSONL event containing `command`, `action`, `timestamp`, and `outcome`. Existing stdout and exit codes are preserved, and audit-write failures cannot replace the command result.

Audit destinations use descriptor-relative traversal with `O_NOFOLLOW`, reject symlinked path components and non-regular files, use nonblocking open, and fail closed if no-follow support is unavailable. Parser construction is shared between execution and audit discovery.

## Changed files

- `src/forgecode_agent/cli.py`
- `tests/unit/test_cli_audit_logging.py`
- `rooms/reviews/2026-08-12-structured-cli-logging.md`

## Verification

- Strict TDD RED evidence captured by implementer for the initial feature and later FIFO/security/portability regressions.
- Focused audit tests: **10 passed**.
- Full suite: **298 passed**.
- `python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- Static added-line security scan: no findings.
- Independent spec review: **PASS**.
- Independent quality/security review after fixes: **APPROVED**.
- Wheel build check: blocked because the environment lacks the `build` module; no code failure observed.

## Status

Ready for orchestrator-owned local commit and push. No unrelated working-tree changes were present before this slice.

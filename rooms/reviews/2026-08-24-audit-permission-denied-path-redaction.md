# Sprint Tick Review: audit permission-denied path redaction

Date: 2026-08-24

## Selected slice

Harden `forgecode audit` so a realistic `PermissionError` carrying the audit-log path cannot disclose sensitive path components or audit payloads. Preserve the existing missing-log and other audit error behavior.

## Changed files

- `src/forgecode_agent/cli.py` — handle `PermissionError` before generic `OSError` formatting and emit the constant path-free message `audit log unavailable: permission denied`.
- `tests/unit/test_cli_audit.py` — add a capability-gated regression with a path-bearing `PermissionError`, exact transcript comparison, one-time denial-hook assertion, and path/payload/traceback non-disclosure checks.
- `tests/golden/audit_permission_denied_path.txt` — deterministic sanitized transcript.

No secrets, credentials, network calls, or unrelated files were involved.

## TDD evidence

- RED: with the new test in place and the production `PermissionError` branch temporarily removed, the focused test failed as expected and exposed `customer-secret-token/audit.jsonl` in the output.
- GREEN: restoring the minimal branch made the focused regression pass.
- Refactor/revision: no assertion changes were needed; `git diff --check` passed.

## Independent review

- Spec-compliance review: PASS.
- Code-quality/security review: APPROVED after TDD evidence re-verification; no critical or important issues remain.
- Final integration review: PASS; scope and fixture references are consistent.

## Verification

- Focused audit tests: passed (`2 passed` for the permission-denial cases).
- Full pytest suite: passed (`367 passed`).
- Ruff: reports two pre-existing unrelated `F841` findings at `src/forgecode_agent/cli.py:522` and `tests/unit/test_cli_init.py:207`; no new findings from this slice.
- `git diff --check`: passed.
- Wheel packaging: passed via `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` (`forgecode_agent-0.0.0-py3-none-any.whl`).
- Added-line hardcoded-secret scan: no findings.

Status: verified and ready for local commit and push.

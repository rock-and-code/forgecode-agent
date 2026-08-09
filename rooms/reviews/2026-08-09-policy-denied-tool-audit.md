# Sprint Tick Review: policy-denied tool audit event

## Selected slice

Record a sanitized `tool_call_failed` ledger event when a known tool request is denied by policy before `run_completed`.

## Files changed

- `src/forgecode_agent/agent.py` — appends `tool_call_failed` with `tool` and `reason` for policy-denied known tools.
- `tests/unit/test_agent_controller.py` — updates supervised shell-tool denial coverage to require the new event ordering and sanitized metadata.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_agent_controller.py::test_agent_controller_stops_safely_when_supervised_policy_denies_known_shell_tool` failed after the test expected `tool_call_failed` before implementation.
- GREEN: focused test passed after implementation (`1 passed`).
- Agent controller suite: `python -m pytest -q tests/unit/test_agent_controller.py` passed (`14 passed`).

## Verification

- Full suite: `python -m pytest -q` passed (`84 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.
- Static added-line security scan: no findings.

## Reviews

- Spec review: PASS.
- Quality review: APPROVED.
- Independent pre-commit review: passed with no security concerns or logic errors.

## Notes

Denied event metadata intentionally excludes denied arguments and command text to avoid leaking sensitive payloads into audit records.

## Next recommended slice

Add a similarly narrow audit-path hardening slice for invalid argument denials if product semantics should distinguish policy denials from schema denials in the ledger, or move to secret-file deny patterns from Epic H2.

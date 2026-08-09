# Sprint Tick Review: invalid tool argument audit event

## Selected slice

Record a sanitized `tool_call_failed` ledger event when a registered tool request is denied because its arguments fail schema validation.

## Files changed

- `src/forgecode_agent/agent.py` — appends `tool_call_failed` with `tool` and `reason` for invalid tool arguments before `run_completed`.
- `tests/unit/test_agent_controller.py` — adds focused sanitization coverage and updates existing invalid-argument event-order assertions.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_agent_controller.py::test_agent_controller_records_sanitized_tool_call_failed_for_invalid_arguments` failed before implementation because `tool_call_failed` was missing before `run_completed`.
- GREEN: the same focused test passed after the minimal implementation (`1 passed`).
- Related invalid-argument checks: `3 passed` for the malformed read-only, malformed shell, and new sanitization tests.

## Verification

- `python -m pytest -q` passed (`92 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED.

## Notes / next recommended slice

Invalid arguments for known tools are still present in earlier `model_responded` / `tool_call_requested` events by existing behavior. A future privacy-hardening slice could decide whether those broader event payloads should also be redacted for schema-denied calls.

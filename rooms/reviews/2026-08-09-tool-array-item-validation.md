# Sprint Tick Review: tool array item schema validation

## Selected slice

ToolRegistry schema hardening: validate JSON Schema array `items.type` before executing handlers, while preserving untyped array behavior.

## Files changed

- `src/forgecode_agent/tools.py` — factors primitive type checks into `_value_matches_type` and applies them to array `items.type` validation.
- `tests/unit/test_tool_registry.py` — adds coverage for string item mismatch, integer array bool rejection, and boolean item mismatch before handler execution.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_array_item_type_mismatch_before_handler_runs` failed before implementation with `Failed: DID NOT RAISE <class 'forgecode_agent.tools.ToolCallDenied'>`.
- GREEN: the focused string-array test passed after minimal implementation.
- Review fix coverage: added integer/boolean array item tests; focused command passed (`3 passed`).
- Tool registry suite: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`20 passed`).

## Verification

- Full suite: `python -m pytest -q` passed (`82 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.
- Static security scan on added lines: no findings.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit review: passed; no security concerns or logic errors.

## Next recommended slice

Continue schema hardening with a similarly narrow test for array constraints such as `minItems`/`maxItems`, or move to a controller edge case around denied tool-call ledger details.

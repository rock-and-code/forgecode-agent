# Sprint Tick Review: tool object property validation

## Selected slice

Reject object-schema tool arguments whose property value is declared as JSON-schema type `object` but is not a dict/object.

## Files changed

- `src/forgecode_agent/tools.py` — enforces property-level `object` type validation with `isinstance(value, dict)`.
- `tests/unit/test_tool_registry.py` — adds a regression test proving non-object metadata is denied before the handler runs.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_object_argument_type_mismatch_before_handler_runs` failed before implementation because `ToolCallDenied` was not raised.
- GREEN: the same focused test passed after the minimal implementation (`1 passed`).
- Tool registry suite: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`24 passed`).

## Verification

- `python -m pytest -q` passed (`98 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.
- `git diff --check` passed.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit diff review: passed with no security concerns or logic errors.
- Final integration review: PASS.

## Notes

A future small slice can add nested object property validation for required keys/properties inside nested object schemas if product needs deeper JSON-schema coverage.

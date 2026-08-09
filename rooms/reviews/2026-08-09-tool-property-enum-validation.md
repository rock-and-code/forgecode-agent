# Sprint Tick Review: tool property enum validation

## Selected slice

Reject object-schema tool arguments whose property value is not included in that property's `enum` constraint.

## Files changed

- `src/forgecode_agent/tools.py` — enforces property-level enum membership after primitive type validation.
- `tests/unit/test_tool_registry.py` — adds a regression test proving invalid enum values are denied before the handler runs.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_object_property_string_not_in_enum_before_handler_runs` failed before implementation because `ToolCallDenied` was not raised.
- GREEN: the same focused test passed after the minimal implementation.
- Tool registry suite: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`23 passed`).

## Verification

- `python -m pytest -q` passed (`96 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit diff review: passed with no security concerns or logic errors.

## Notes

A future small slice can add positive-path enum coverage or extend enum checks to top-level array item schemas if product needs that behavior.

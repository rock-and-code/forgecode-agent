# Sprint Tick Review: ToolRegistry array schema validation

## Selected slice

Harden malformed tool-argument handling for top-level array schemas in `ToolRegistry`.

## Files changed

- `src/forgecode_agent/tools.py` — honors `parameters={"type": "array"}` by requiring list arguments and passing valid lists to handlers as one positional argument.
- `tests/unit/test_tool_registry.py` — adds denial and success coverage for top-level array schemas.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_dict_for_array_schema_before_handler_runs` failed before implementation with `Failed: DID NOT RAISE <class 'forgecode_agent.tools.ToolCallDenied'>`.
- GREEN: focused array-schema tests passed after implementation.
- Regression: `python -m pytest -q tests/unit/test_tool_registry.py` passed with `15 passed`.

## Verification

- `python -m pytest -q` — `75 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully.
- `git diff --check` — clean.
- Static security scan on added lines — no findings.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED after adding positive valid-list coverage.
- Final integration review: PASS.
- Independent pre-commit JSON review: passed; no security concerns or logic errors.

## Non-blocking follow-up

If richer JSON Schema support becomes part of the MVP, add item-type and array-constraint validation such as `items`, `minItems`, and `maxItems`.

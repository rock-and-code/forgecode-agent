# Sprint Tick Review: tool object property count validation

## Selected slice

Enforce JSON-schema-like object `minProperties` and `maxProperties` constraints in `ToolRegistry` argument validation.

## Files changed

- `src/forgecode_agent/tools.py` — validates object property counts for top-level, nested, and bare object property-count schemas.
- `tests/unit/test_tool_registry.py` — adds deny/allow coverage for top-level object counts, bare object counts, and nested object counts.

## TDD evidence

- RED: initial focused object-property-count tests failed before implementation because out-of-bounds object argument counts were accepted (`2 failed, 2 passed, 89 deselected`).
- Spec fix RED: a bare-object valid-count regression test failed before the bare-schema fix because valid dicts were denied.
- Nested coverage note: nested tests passed immediately after adding them because the implementation already covered nested schemas through `_value_matches_schema()`.
- GREEN: focused object-property-count tests passed (`7 passed, 89 deselected`); full tool registry suite passed (`96 passed`).

## Verification

- `python -m pytest -q` — `170 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.
- `git diff --check` — passed.
- `ruff check src/forgecode_agent/tools.py tests/unit/test_tool_registry.py` — passed during quality review.

## Review result

- Spec compliance review: PASS after one fix loop for bare object schemas.
- Code quality review: APPROVED after nested coverage/style fix.
- Independent security/logic diff review: PASS (`security_concerns=[]`, `logic_errors=[]`).
- Final integration review: PASS.

## Next recommended slice

Continue schema hardening with another small JSON-schema constraint such as object `dependentRequired`, or move to golden transcript fixture infrastructure.

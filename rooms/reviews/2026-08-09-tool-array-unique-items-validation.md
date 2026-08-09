# Sprint Tick Review: tool array uniqueItems validation

## Selected slice

Enforce top-level array schema `uniqueItems: true` in `ToolRegistry` so duplicate model-supplied array arguments are denied before any tool handler runs.

## Files changed

- `src/forgecode_agent/tools.py` — adds a minimal uniqueness check in array schema validation using existing structural const comparison.
- `tests/unit/test_tool_registry.py` — adds RED/GREEN coverage for duplicate denial and unique-array success.

## TDD evidence

- RED: focused duplicate-array test failed before implementation because `ToolCallDenied` was not raised.
- GREEN: focused uniqueItems tests passed after the minimal validator change (`2 passed`).
- Targeted ToolRegistry suite passed (`65 passed`).

## Verification

- `python -m pytest -q` — `139 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully.
- `git diff --check` — passed.
- `ruff check .` — passed.
- Added-line security scan — no hardcoded secret, shell injection, eval/exec, pickle, or SQL string-format findings.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit JSON review: passed; no security concerns or logic errors.
- Final integration review: APPROVED.

## Next recommended slice

If schema hardening continues, add a narrow follow-up test for `uniqueItems` on array items containing objects/lists, or move to golden transcript fixture infrastructure.

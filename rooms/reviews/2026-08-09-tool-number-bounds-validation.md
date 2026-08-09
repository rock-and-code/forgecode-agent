# Sprint Tick Review: tool number bounds validation

## Selected slice

Enforce JSON-schema `minimum`/`maximum` constraints for `type: "number"` tool arguments while preserving existing integer bounds and number type behavior.

## Files changed

- `src/forgecode_agent/tools.py` — applies min/max checks to both `integer` and `number` schema types.
- `tests/unit/test_tool_registry.py` — adds out-of-range denial coverage and boundary/in-range allow coverage for number bounds.

## TDD evidence

- RED: `pytest tests/unit/test_tool_registry.py -k 'number_argument_bounds'` failed before implementation (`2 failed, 3 passed, 44 deselected`) because out-of-range numbers did not raise `ToolCallDenied`.
- GREEN: focused bounds tests passed after the minimal validator change (`5 passed, 44 deselected`).
- Tool registry suite: `pytest tests/unit/test_tool_registry.py` passed (`49 passed`).

## Verification

- Spec review: PASS.
- Quality review: APPROVED.
- Independent pre-commit review: PASS; no security concerns or logic errors.
- Static scan: no hardcoded secret, shell injection, eval/exec, pickle, or SQL string-format findings in added lines.
- `git diff --check`: passed.
- `ruff check .`: passed.
- `python -m pytest -q`: passed (`123 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check`: passed; wheel built successfully.

## Notes / next slice

Continue ToolRegistry schema hardening with another narrow validation follow-up such as numeric bounds for top-level array item schemas if needed, or move to golden transcript fixture infrastructure.

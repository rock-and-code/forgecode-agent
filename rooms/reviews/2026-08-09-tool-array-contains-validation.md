# Sprint Tick Review: tool array contains validation

## Selected slice

Add JSON Schema array `contains`, `minContains`, and `maxContains` validation to `ToolRegistry` so model-supplied array arguments are denied before any tool handler runs when required contained items are missing or count constraints are violated.

## Files changed

- `src/forgecode_agent/tools.py` — adds array `contains` matching/count validation and recursive fail-safe detection for malformed array-contains settings.
- `tests/unit/test_tool_registry.py` — adds regression coverage for default `contains`, `minContains`/`maxContains`, malformed settings, nullable schema bypasses, `anyOf` bypasses, and nested schema cases.

## TDD evidence

- Initial RED: `python -m pytest -q tests/unit/test_tool_registry.py -k 'contains'` failed before implementation (`8 failed, 1 passed, 136 deselected`).
- Spec-fix RED: focused malformed nullable/maxContains tests failed before fixes (`5 failed, 5 passed, 140 deselected`).
- Quality-fix RED: malformed `anyOf` bypass tests failed before fixes (`2 failed, 150 deselected`).
- Recursive spec-fix RED: optional nested-property / unmatched-branch malformed tests failed before fixes (`2 failed, 1 passed, 152 deselected`).
- Final focused GREEN: `pytest tests/unit/test_tool_registry.py -k contains` passed (`19 passed, 136 deselected`).
- Final tool-registry GREEN: `pytest tests/unit/test_tool_registry.py` passed (`155 passed`).

## Verification

- Spec review: PASS.
- Quality review: APPROVED.
- Full suite: `python -m pytest -q` passed (`229 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.
- Static diff checks: no whitespace errors or obvious secret/shell/eval/pickle/SQL patterns found.

## Notes

Malformed array-contains settings are validated recursively across `anyOf`, `properties`, `items`, `additionalProperties`, `dependentSchemas`, and nested `contains` schemas to avoid handler execution from invalid tool schemas.

## Next recommended slice

Move to golden transcript fixture infrastructure, or continue schema hardening only if planned MVP tool schemas require another JSON Schema keyword.

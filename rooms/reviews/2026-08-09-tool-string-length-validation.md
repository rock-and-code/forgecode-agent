# Sprint Tick Review: tool string length validation

## Selected slice

ToolRegistry schema hardening: deny object-property string arguments that violate `minLength` or `maxLength` before handler execution.

## Files changed

- `src/forgecode_agent/tools.py` — enforces string property `minLength` / `maxLength` constraints inside existing argument validation.
- `tests/unit/test_tool_registry.py` — adds negative denial coverage plus boundary/in-range allow coverage.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_object_property_string_length_constraints_before_handler_runs` failed before implementation (`2 failed`) because too-short/too-long string values were accepted.
- GREEN: the same focused test passed after minimal validation (`2 passed`).
- Quality fix coverage: focused changed tests passed (`5 passed`).

## Verification

- `python -m pytest -q` — passed (`103 passed`).
- `ruff check .` — passed.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.
- Static added-line security scans — no findings.

## Review result

- Spec review: PASS.
- Quality review: APPROVED after adding positive/boundary tests.
- Independent pre-commit review: passed with no security concerns or logic errors.

## Next recommended slice

Continue tool schema hardening with a similarly narrow constraint, such as numeric `minimum`/`maximum` for integer properties, or move to a controller audit/privacy follow-up for redacting invalid argument payloads from broader model/tool request events.

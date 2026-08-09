# Sprint Tick Review: tool dependentSchemas validation

## Selected slice

Add JSON Schema object `dependentSchemas` validation to `ToolRegistry` so model-supplied tool arguments are denied before handler execution when a triggered dependent subschema does not match the whole object.

## Files changed

- `src/forgecode_agent/tools.py` — enforces `dependentSchemas`, evaluates triggered subschemas against the whole object through the recursive schema validator, and keeps no-explicit-type object schemas from bypassing general constraints such as `enum`/`const`.
- `tests/unit/test_tool_registry.py` — adds regression coverage for top-level and nested `dependentSchemas`, malformed definitions, bare object and `anyOf` dependent schemas, no-explicit-type object subschemas, and top-level general-constraint fail-open cases.

## TDD evidence

- Initial RED: focused `dependentSchemas` tests failed before implementation (`2 failed, 4 passed`) because top-level and nested dependent schema violations were allowed.
- Spec-gap RED: whole-object dependent subschema tests failed before fix (`2 failed`) because bare-object/`anyOf` dependent schemas were routed through an object-only path.
- AnyOf object-keyword RED: no-explicit-type object subschema inside `anyOf` failed before fix (`1 failed`) because it passed through instead of validating object keywords.
- Quality regression RED: no-explicit-type object subschema plus `enum` failed open before fix (`1 failed`).
- Top-level regression RED: top-level no-type `dependentSchemas` plus `enum` failed open before fix (`1 failed`).
- GREEN: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`136 passed`).

## Verification

- `python -m pytest -q` — `210 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — successfully built `forgecode_agent-0.0.0-py3-none-any.whl`.
- `git diff --check` — clean.
- Static added-line security scan — no findings for hardcoded secrets, shell injection, eval/exec, unsafe pickle, or SQL string-format patterns.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED with no critical, important, or minor issues.

## Next recommended slice

Continue schema hardening with a narrow `contains`/`minContains` array validation slice, or move to golden transcript fixture infrastructure if schema coverage is sufficient for the current MVP.

# Sprint Tick Review: tool dependentRequired validation

## Selected slice

Enforce JSON Schema object `dependentRequired` constraints in `ToolRegistry` so model-supplied tool arguments are denied before any handler runs when dependent fields are missing.

## Files changed

- `src/forgecode_agent/tools.py` — validates `dependentRequired` for top-level and nested object schemas, including dependency-only object schemas.
- `tests/unit/test_tool_registry.py` — adds regression coverage for missing dependencies, satisfied dependencies, dependency-only schemas, and nested object dependencies.
- `rooms/reviews/2026-08-09-tool-dependent-required-validation.md` — records this sprint tick handoff.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py -k dependent_required` failed before implementation with missing denials (`DID NOT RAISE ToolCallDenied`).
- Review-gap RED: `pytest tests/unit/test_tool_registry.py -k dependency_only_dependent_required -q` failed before the follow-up fix because a dependency-only object schema rejected a satisfied dependency.
- GREEN: focused dependent-required tests passed after implementation (`3 passed`, then dependency-only regression `1 passed`).
- Tool registry suite: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`116 passed`).

## Verification

- `python -m pytest -q` passed (`190 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.
- `git diff --check` passed.
- Added-line static scan found no hardcoded secret, shell injection, eval/exec, pickle, or SQL-formatting findings.

## Review result

- Spec review initially found a dependency-only object-schema gap; fixed with a focused regression.
- Re-run spec review: PASS.
- Re-run quality review: APPROVED.
- Independent pre-commit reviewer JSON: passed with no security concerns or logic errors.

## Next recommended slice

Continue schema hardening with a narrow `dependentSchemas` or array `contains` validation slice, or move to golden transcript fixture infrastructure.

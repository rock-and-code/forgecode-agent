# Sprint Tick Review: tool allOf validation

## Selected slice

Add JSON Schema `allOf` validation to `ToolRegistry` so model-supplied tool arguments are denied before any handler runs unless every subschema matches.

## Files changed

- `src/forgecode_agent/tools.py` — validates `allOf` recursively, rejects malformed `allOf`, traverses `allOf` subschemas for existing keyword validation, and handles top-level allOf-only / typed-object allOf forms.
- `tests/unit/test_tool_registry.py` — adds focused coverage for nested property allOf, malformed allOf, top-level allOf-only, typed-object allOf, and annotation/meta siblings.

## TDD evidence

- RED: initial `python -m pytest -q tests/unit/test_tool_registry.py -k 'all_of'` failed before implementation (`4 failed, 1 passed`) because `allOf` was not enforced.
- GREEN: focused allOf tests passed after minimal recursive validation.
- RED/GREEN follow-ups caught and fixed top-level allOf-only schemas, annotation/meta siblings, and top-level `type: "object"` + `allOf`.
- Final focused check: `python -m pytest -q tests/unit/test_tool_registry.py -k 'all_of'` passed (`12 passed, 165 deselected`).

## Verification

- `python -m pytest -q` passed (`251 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` passed.
- `git diff --check` passed.
- Static added-line security scan found no hardcoded secrets, shell injection, eval/exec, pickle, or SQL formatting patterns.

## Review result

- Spec review: PASS.
- Quality review: APPROVED after focused fix loops.
- Independent pre-commit diff review was attempted but the reviewer subagent hit an API 429 usage limit. Existing independent spec/quality reviews and local verification passed.

## Next recommended slice

Continue with golden transcript fixture infrastructure, or add another small controller/ToolRegistry hardening case only if required by planned MVP tool schemas.

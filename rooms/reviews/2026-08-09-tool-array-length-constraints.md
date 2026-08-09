# Sprint Tick Review: tool array length constraints

## Selected slice

Enforce top-level JSON Schema array `minItems` and `maxItems` constraints in `ToolRegistry` argument validation.

## Files changed

- `src/forgecode_agent/tools.py` — denies arrays shorter than `minItems` or longer than `maxItems` before item validation/handler execution.
- `tests/unit/test_tool_registry.py` — adds regression coverage for below-minimum and above-maximum array lengths.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_tool_registry.py::test_tool_registry_denies_array_length_constraints_before_handler_runs` failed before implementation with `2 failed`; both cases reported `DID NOT RAISE ToolCallDenied`, proving the invalid arrays were accepted.
- GREEN: the same focused test passed after the minimal validation change (`2 passed`).
- Tool registry suite: `python -m pytest -q tests/unit/test_tool_registry.py` passed (`22 passed`).

## Verification

- Full test suite: `python -m pytest -q` passed (`84 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` successfully built `forgecode_agent-0.0.0-py3-none-any.whl`.
- Static security scan of added lines: no findings.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED; non-blocking suggestions only.
- Independent pre-commit review: PASS; no security concerns or blocking logic errors.

## Next recommended slice

Add another narrow schema-hardening test, such as a positive constrained-array boundary case or object property enum/constant validation if it is needed for MVP tool safety.

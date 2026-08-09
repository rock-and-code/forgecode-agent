# Sprint Tick Review: budget exhaustion before multiple tool calls

## Selected slice

Prioritize exhausted `AgentController.max_iterations` over multiple-tool-call classification when the model asks for tools while the budget is already zero.

## Files changed

- `src/forgecode_agent/agent.py` — checks exhausted iteration budget before rejecting multiple tool intents, after preserving no-tool final answers.
- `tests/unit/test_agent_controller.py` — adds regression coverage for `max_iterations=0` with multiple requested tools.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_agent_controller.py::test_agent_controller_prioritizes_max_iterations_zero_before_multiple_tool_calls` failed before implementation because the controller returned `stop_reason="multiple_tool_calls"`.
- GREEN: the same focused test passed after the minimal controller ordering change.
- Regression: `python -m pytest -q tests/unit/test_agent_controller.py` passed with `17 passed`.

## Verification

- `python -m pytest -q` — `97 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully.
- Static security scan on added lines — no findings.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit JSON review: passed; no security concerns or logic errors.

## Non-blocking follow-up

Continue budget/loop hardening with another narrow terminal-state precedence case, or move to golden transcript infrastructure/context compaction tests.

# Sprint Tick Review: safe tool handler runtime failures

## Selected slice

Handle registered tool handler runtime exceptions safely: record sanitized failure metadata, stop the agent loop with `stop_reason="tool_error"`, avoid another model request, and prevent raw exception messages from leaking into ledger/call history.

## Files changed

- `src/forgecode_agent/tools.py` — adds `ToolExecutionError`; wraps handler exceptions with safe `error_type` metadata and failed call history.
- `src/forgecode_agent/agent.py` — catches `ToolExecutionError`, records `tool_call_failed`, and returns an incomplete `AgentRunResult` with `tool_error`.
- `tests/unit/test_agent_controller.py` — adds controller coverage for safe stop/no extra model request/no secret-bearing exception leakage.
- `tests/unit/test_tool_registry.py` — adds direct registry coverage for wrapping handler failures without leaking raw messages.

## TDD evidence

- RED: `pytest tests/unit/test_agent_controller.py::test_agent_controller_stops_safely_when_tool_handler_raises_runtime_exception tests/unit/test_tool_registry.py::test_tool_registry_wraps_handler_failures_without_leaking_raw_message -q` failed before implementation due to missing `ToolExecutionError` / raw exception behavior.
- GREEN: same focused tests passed with `2 passed` after minimal implementation.
- Regression: `pytest tests/unit/test_agent_controller.py::test_agent_controller_stops_safely_when_tool_handler_raises_runtime_exception tests/unit/test_tool_registry.py -q` passed with `17 passed`; full suite passed with `78 passed`.

## Verification

- `python -m pytest -q` — `78 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully (`forgecode_agent-0.0.0-py3-none-any.whl`).
- `git diff --check` — clean.
- `ruff check .` — all checks passed.
- Static security scan on added lines — no findings.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED after fix loop.
- Independent pre-commit JSON review: passed; no security concerns or logic errors.

## Non-blocking follow-up

Consider documenting that `ToolExecutionError.__cause__` preserves the original exception for in-process debugging while ledger/call-history fields remain sanitized.

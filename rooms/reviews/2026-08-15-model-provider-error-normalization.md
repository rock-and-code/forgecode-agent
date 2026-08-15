# Sprint Tick Review: model-provider error normalization

- **Selected slice:** Normalize exceptions from `model_provider.complete()` into a safe terminal `AgentRunResult`.
- **Changed files:** `src/forgecode_agent/agent.py`, `tests/unit/test_agent_controller.py`.
- **Implementation:** Provider failures now emit sanitized `model_error` metadata containing only the exception type, append terminal `run_completed`, preserve the last safe answer, return `completed=False` with `stop_reason="model_error"`, and stop without retrying.
- **TDD evidence:** Added a regression test first; the focused test initially failed because `RuntimeError` escaped. After the minimal implementation, focused test passed and verified exactly two provider requests, safe fallback, terminal ledger events, and no raw exception payload.
- **Verification:** Full suite: **324 passed**. `python -m compileall -q src tests`: passed. `git diff --check`: passed. Static security scan: no findings. Spec review: PASS. Independent quality/security review: APPROVED.
- **Build:** Wheel build skipped because neither `hatch` nor the `build` module is installed in this environment.
- **Status:** Ready for parent commit and push. No secrets, network calls, or unrelated files included.

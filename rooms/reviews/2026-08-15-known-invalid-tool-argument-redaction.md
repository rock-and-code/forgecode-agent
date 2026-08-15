# Sprint Tick Review: known-tool invalid-argument redaction

- **Selected slice:** Redact malformed arguments for known tools from controller audit events before they are serialized.
- **Changed files:** `src/forgecode_agent/agent.py`, `tests/unit/test_agent_controller.py`.
- **Implementation:** When schema validation rejects a known tool call, the latest `model_responded` and `tool_call_requested` event arguments are replaced with `[REDACTED]`; existing `invalid_tool_arguments` termination, unknown-tool behavior, and valid-call logging remain unchanged.
- **TDD evidence:** Added the regression test first. Focused RED run failed because malformed known-tool arguments remained in `model_responded`; minimal implementation then produced GREEN. Focused/related tests: 6 passed. Full suite: **325 passed**.
- **Verification:** `python -m compileall -q src tests` passed; `git diff --check` passed; independent spec review PASS; quality review APPROVED; independent security/logic review passed with no blocking findings.
- **Build:** Wheel build not available because the `build` module is not installed in this environment.
- **Status:** Ready for orchestrator commit and push. No secrets, network calls, or unrelated files included.

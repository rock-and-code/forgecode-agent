# Review: malformed model-response normalization

Date: 2026-08-18
Slice: Fail-closed handling for malformed successful model-provider responses.

## Scope

`AgentController.run()` now validates provider responses before ledger serialization or tool execution. Invalid responses and malformed tool-intent arguments (non-dict, non-JSON-safe, non-string nested mapping keys, or cyclic containers) terminate safely with `stop_reason=model_error`, preserve the last safe answer, and emit sanitized terminal events.

## Evidence

- TDD RED evidence recorded by implementer subagents for malformed response, non-dict arguments, nested non-string keys, and cyclic arguments.
- Focused controller tests passed.
- Full suite: `344 passed`.
- `python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- Independent spec review: PASS.
- Independent code-quality review: APPROVED after cycle-safety fix.
- Pre-existing lint findings remain outside this slice (`F841` in `src/forgecode_agent/cli.py:517` and `tests/unit/test_cli_init.py:207`).
- Packaging check was attempted but blocked by the environment: `python -m build` is unavailable and the local build environment lacks `hatchling`; no source changes resulted.

## Files

- `src/forgecode_agent/agent.py`
- `tests/unit/test_agent_controller.py`

Status: approved for local commit and push.

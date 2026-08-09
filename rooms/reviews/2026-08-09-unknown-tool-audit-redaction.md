# Sprint Tick Review: unknown-tool audit redaction

## Selected slice

Audit and redact model-requested unknown tool calls so failed unknown-tool requests are traceable without persisting unknown payload arguments.

## Files changed

- `src/forgecode_agent/agent.py` — redacts unknown-tool arguments in `model_responded` and `tool_call_requested` ledger data; appends sanitized `tool_call_failed` before `run_completed`.
- `tests/unit/test_agent_controller.py` — updates unknown-tool event sequence expectations and adds serialized-ledger regression coverage for secret-like unknown-tool payloads.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_agent_controller.py::test_agent_controller_stops_safely_for_unknown_tools tests/unit/test_agent_controller.py::test_agent_controller_stops_safely_for_unknown_tools_with_non_dict_arguments` failed before implementation because `tool_call_failed` was missing.
- RED fix loop: `pytest tests/unit/test_agent_controller.py::test_agent_controller_redacts_unknown_tool_arguments_from_serialized_ledger -q` failed before redaction because the secret-like payload appeared in serialized ledger data.
- GREEN: focused unknown-tool tests passed after implementation.
- GREEN: `python -m pytest -q` passed (`85 passed`).

## Verification

- `python -m pytest -q` — passed (`85 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — passed; built `forgecode_agent-0.0.0-py3-none-any.whl`.
- `git diff --check` — passed.
- Static scan for hardcoded secrets/shell injection/eval/pickle/SQL-string patterns — no findings.

## Review result

- Spec compliance review: PASS.
- Quality review: initially requested changes for unknown-tool argument leakage via non-failure ledger events; fix applied.
- Quality re-review: approved.
- Final integration review: APPROVED.

## Notes

Unknown tool failure metadata intentionally records only tool name and reason. Unknown arguments are redacted with the shared ledger redaction marker before ledger serialization.

## Next recommended slice

Add a similarly narrow audit-path hardening slice for invalid argument denials, or continue CLI `doctor` polish/status output coverage.

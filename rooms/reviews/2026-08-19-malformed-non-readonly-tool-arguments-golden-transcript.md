# Sprint Tick Review: malformed non-read-only tool arguments golden transcript

Date: 2026-08-19

## Selected slice

Add deterministic golden-transcript coverage for the existing `AgentController` terminal path when a known non-read-only `run_shell` tool receives non-dict arguments. The regression proves malformed model data fails closed before tool execution, records `MalformedModelResponse`, preserves the safe goal answer, and matches the normalized ledger transcript.

## Changed files

- `tests/unit/test_agent_controller.py` — adds the focused golden-transcript test and verifies the handler, registry, and provider are not executed beyond the first request.
- `tests/golden/malformed_non_readonly_tool_arguments_terminal.json` — records the expected deterministic terminal transcript.
- This review artifact.

No production behavior changed.

## TDD evidence

- RED: focused test initially failed with the expected `FileNotFoundError` because the new golden fixture was absent.
- GREEN: focused test passed after adding the minimal fixture (`1 passed`).

## Review and verification

- Spec-compliance review: PASS.
- Independent code-quality/security review: APPROVED; no critical or important issues.
- Final integration review: APPROVED.
- Focused controller tests: `python -m pytest --tb=no -q tests/unit/test_agent_controller.py` — **43 passed**.
- Full suite: `python -m pytest --tb=no -q` — **350 passed**.
- `python -m compileall -q src tests` — passed.
- `git diff --check` — passed.
- Packaging: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — passed.
- Added-line static security scan — no findings.
- Ruff reports two pre-existing F841 findings outside this slice (`src/forgecode_agent/cli.py:517`, `tests/unit/test_cli_init.py:207`); no new findings.

Status: approved for local commit and push.

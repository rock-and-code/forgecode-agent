# Sprint Tick Review: golden transcript for model-provider errors

- **Selected slice:** Add deterministic golden transcript coverage for the `AgentController` model-provider-error terminal branch, the next focused controller QA slice after existing read, budget, multiple-tool, and policy-denial transcripts.
- **Changed files:** `tests/unit/test_agent_controller.py`, `tests/golden/model_error_terminal.json`, this review artifact.
- **Implementation:** Added a test provider that raises `RuntimeError`, runs the controller, removes timestamps, and compares the resulting `run_started`, `model_requested`, `model_error`, and `run_completed` events with the new fixture. No production code changed.

## TDD evidence

- **RED:** Focused test failed with `FileNotFoundError` because `tests/golden/model_error_terminal.json` did not exist.
- **GREEN:** Focused test passed after adding the minimal fixture (`1 passed`).
- **Full suite:** `python -m pytest --tb=no -q` → **328 passed**.

## Verification

- `python -m compileall -q src tests` — passed.
- `git diff --check` — passed.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — passed.
- Static added-line security scan — no findings.
- Ruff — two pre-existing F841 findings remain outside this slice (`src/forgecode_agent/cli.py:517`, `tests/unit/test_cli_init.py:207`); no new findings.
- Independent spec review — **PASS**.
- Independent quality/security review — **APPROVED**.
- Independent pre-commit JSON review — **passed**, no security concerns or logic errors.

No secrets, network calls, destructive commands, or unrelated source changes were included. Ready for orchestrator commit and push.

# Sprint Tick Review: negative max_iterations validation

## Selected slice

Reject invalid negative `AgentController.max_iterations` values at construction time while preserving existing zero-budget behavior.

## Files changed

- `src/forgecode_agent/agent.py` — adds `__post_init__` validation that raises `ValueError` when `max_iterations < 0`.
- `tests/unit/test_agent_controller.py` — adds coverage for negative max-iteration construction failure.

## TDD evidence

- RED: `python -m pytest tests/unit/test_agent_controller.py::test_agent_controller_rejects_negative_max_iterations -q` failed before implementation with `Failed: DID NOT RAISE <class 'ValueError'>`.
- GREEN: same focused test passed after minimal implementation.
- Regression: `python -m pytest tests/unit/test_agent_controller.py -q` passed with `13 passed`.

## Verification

- `python -m pytest -q` — `76 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully.
- `git diff --check` — clean.
- Static security scan on added lines — no findings.
- `ruff check .` — all checks passed.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit JSON review: passed; no security concerns or logic errors.

## Non-blocking follow-up

Consider a later configuration/CLI validation slice if `max_iterations` becomes user-configurable from command-line flags or config files.

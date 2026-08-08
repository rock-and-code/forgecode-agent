# Sprint Tick Review: CLI doctor argument parsing

## Selected slice

MVP Slice 1 next test: CLI `main` argument parsing for `forgecode doctor`.

## Outcome

Approved for local commit.

## Files changed

- `src/forgecode_agent/cli.py` — added minimal `argparse` handling for the `doctor` subcommand and `--workspace` option.
- `tests/unit/test_cli_doctor.py` — added focused CLI argument parsing tests.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_cli_doctor.py` failed before implementation with missing CLI argument parsing behavior.
- GREEN: `python -m pytest -q tests/unit/test_cli_doctor.py` passed after implementation (`5 passed`).

## Reviews

- Spec compliance review: PASS.
- Code quality/security review: APPROVED.
- Pre-commit JSON review: passed with no security concerns or logic errors.
- Final integration/evaluator review: APPROVED.

## Gates

- `python -m pytest -q` — `34 passed`.
- `python -m pip wheel . --no-deps` to a temporary `/tmp` directory — wheel built successfully; temporary artifacts removed.

## Approval notes

No human approval is needed for the local commit. Human approval remains required before push, publish, external side effects, or destructive operations.

# Sprint Tick Review: ledger JSONL timestamp validation

## Selected slice

Ledger persistence hardening: reject JSONL ledgers whose event timestamps are not contiguous in file order starting at `0`.

## Files changed

- `src/forgecode_agent/ledger.py` — validates timestamp sequence during `RunLedger.read_jsonl`.
- `tests/unit/test_run_ledger.py` — adds regression coverage for non-contiguous timestamps.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_non_contiguous_timestamps_in_file_order` failed before implementation because invalid timestamps were accepted.
- GREEN: the same focused test passed after the minimal validation change.
- Ledger suite: `python -m pytest -q tests/unit/test_run_ledger.py` passed (`10 passed`).

## Verification

- `python -m pytest -q` passed (`48 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` built `forgecode_agent-0.0.0-py3-none-any.whl` successfully.

## Review

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent security/logic diff review: passed with no security concerns or logic errors.

## Next recommended slice

Add another narrow ledger reload hardening test, such as rejecting missing required JSONL row keys or non-integer timestamp values.

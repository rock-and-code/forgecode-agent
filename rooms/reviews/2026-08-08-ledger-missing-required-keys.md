# Sprint Tick Review: ledger JSONL missing required keys

## Selected slice

Ledger persistence hardening: reject JSONL rows missing any required ledger row key (`type`, `data`, `timestamp`, or `run_id`) with a clear `ValueError` instead of leaking raw indexing errors.

## Files changed

- `src/forgecode_agent/ledger.py` — validates required JSONL row keys before indexing parsed rows.
- `tests/unit/test_run_ledger.py` — adds parametrized coverage for each missing required key.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_rows_missing_required_keys` failed before implementation with raw `KeyError` for missing row keys.
- GREEN: the same focused test passed after adding minimal validation (`4 passed`).
- Ledger suite: `python -m pytest -q tests/unit/test_run_ledger.py` passed (`14 passed`).

## Verification

- Full suite: `python -m pytest -q` passed (`54 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.
- Spec review: PASS.
- Quality review: APPROVED.
- Independent pre-commit review: PASS; one non-blocking suggestion to consider a future test for non-object JSONL rows.

## Next recommended slice

Add another narrow ledger reload hardening test: reject JSONL rows that parse successfully but are not objects (for example arrays or strings) with `ValueError` instead of an attribute error.

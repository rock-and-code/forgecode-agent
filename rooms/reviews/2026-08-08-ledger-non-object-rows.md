# Sprint Tick Review: ledger JSONL non-object rows

## Selected slice

Ledger persistence hardening: reject JSONL rows that parse successfully but are not objects (arrays, strings, numbers) with a clear `ValueError` instead of leaking an attribute error during required-key validation.

## Files changed

- `src/forgecode_agent/ledger.py` — validates each parsed JSONL row is a dict/object before checking required keys.
- `tests/unit/test_run_ledger.py` — adds parametrized coverage for array, string, and number JSONL rows.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_non_object_rows` failed before implementation with `AttributeError` from `row.keys()`.
- GREEN: the same focused test passed after adding minimal row type validation (`3 passed`).
- Ledger suite: `python -m pytest -q tests/unit/test_run_ledger.py` passed (`17 passed`).

## Verification

- Full suite: `python -m pytest -q` passed (`57 passed`).
- Wheel build: `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` succeeded.
- Static scan: no added-line findings for hardcoded secrets, shell injection, eval/exec, pickle deserialization, or SQL formatting.

## Review result

- Spec compliance reviewer: PASS.
- Code quality reviewer: APPROVED.
- Independent pre-commit reviewer: passed with no security concerns or logic errors.

## Next recommended slice

Continue ledger reload hardening with a narrow validation test for malformed row field types, such as non-string `type`, non-dict `data`, or non-integer `timestamp` values.

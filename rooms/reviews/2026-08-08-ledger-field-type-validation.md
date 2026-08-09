# Sprint Tick Review: ledger JSONL field type validation

## Selected slice

Ledger persistence hardening: reject JSONL rows with malformed required field types before reconstructing `LedgerEvent` objects.

## Files changed

- `src/forgecode_agent/ledger.py` — validates `type`, `data`, `timestamp`, and `run_id` field types during `RunLedger.read_jsonl`.
- `tests/unit/test_run_ledger.py` — adds parametrized regression coverage for malformed required field types.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_malformed_required_field_types` failed before implementation (`5 failed`) because malformed rows were accepted or rejected with less-specific downstream errors.
- GREEN: the same focused test passed after minimal validation (`5 passed`).
- Ledger suite: `python -m pytest -q tests/unit/test_run_ledger.py` passed (`22 passed`).

## Verification

- `python -m pytest -q` — `62 passed`.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — wheel built successfully (`forgecode_agent-0.0.0-py3-none-any.whl`).
- Static added-line security scan — no findings.

## Review result

- Spec compliance review: PASS.
- Code quality review: APPROVED.
- Independent pre-commit reviewer JSON verdict: passed with no security concerns or logic errors.

## Next recommended slice

Continue ledger reload hardening with one narrow validation test for malformed JSONL syntax/error messaging or controller/tool-call edge cases such as unknown tool requested by the model.

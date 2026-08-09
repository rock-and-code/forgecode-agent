# Sprint Tick Review: ledger malformed JSONL syntax

## Selected slice

Ledger persistence hardening: `RunLedger.read_jsonl` rejects malformed non-empty JSONL lines with a clear `ValueError` instead of surfacing `json.JSONDecodeError`.

## Files changed

- `src/forgecode_agent/ledger.py` — parses JSONL rows in a loop, skips blank lines as before, and converts malformed JSON syntax into `ValueError` with non-empty row index and physical line number.
- `tests/unit/test_run_ledger.py` — adds malformed JSONL regression tests, including blank-line row/line diagnostics and suppressed exception chaining.

## TDD evidence

- RED: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_malformed_json_lines_with_value_error` failed before implementation because malformed syntax leaked JSON parser behavior / lacked the required JSONL diagnostic.
- RED fix loop: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_malformed_line_reports_non_empty_row_and_physical_line` failed with `malformed jsonl ledger row 2 (line 3)`, proving row numbering was tied to physical line index.
- RED fix loop: `python -m pytest -q tests/unit/test_run_ledger.py::test_read_jsonl_rejects_malformed_json_lines_with_value_error` failed while `ValueError.__cause__` still exposed `JSONDecodeError`.
- GREEN: focused malformed JSONL tests passed after minimal implementation and fixes.
- Ledger suite: `python -m pytest -q tests/unit/test_run_ledger.py` passed (`24 passed`).

## Verification

- `python -m pytest -q` passed (`64 passed`).
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` successfully built `forgecode_agent-0.0.0-py3-none-any.whl`.
- `git diff --check` passed.
- Added-line security scan found no hardcoded secret, shell injection, eval/exec, pickle, or SQL-formatting issues.

## Review result

- Spec/quality review: APPROVED after two focused fix loops.
- Independent pre-commit reviewer: passed; no security concerns or logic errors.
- Final integration reviewer: APPROVED.

## Next recommended slice

Continue ledger reload hardening with another narrow malformed-file edge case, or move to a controller/tool-call edge case such as denied tool-call path or model-requested unknown tool behavior if ledger hardening is sufficient.

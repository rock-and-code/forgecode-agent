# Review: object property count keyword validation

Date: 2026-08-09
Slice: validate invalid `minProperties` / `maxProperties` schema metadata before tool handlers run.

## Summary
- Added RED/GREEN unit coverage for invalid object property count schema keyword values.
- Implemented fail-closed validation for `minProperties` and `maxProperties`:
  - values must be non-bool integers `>= 0`;
  - if both are present, `minProperties <= maxProperties`;
  - invalid root or nested schema metadata denies execution with `invalid_arguments` before the handler runs.

## TDD evidence
- RED: focused test initially failed with 6 failures, including handler execution for invalid metadata and `TypeError` for string keyword values.
- GREEN: `python -m pytest tests/unit/test_tool_registry.py -q -k 'invalid_object_property_count_schema'` passed with 10 tests.
- Regression: `python -m pytest tests/unit/test_tool_registry.py -q` passed with 165 tests.

## Verification
- `python -m pytest -q` -> 239 passed.
- `python -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` -> wheel built successfully.

## Independent review
- Spec compliance: PASS.
- Code quality: APPROVED.
- Reviewer note: helper reuse is behaviorally correct; naming could be polished later if desired.

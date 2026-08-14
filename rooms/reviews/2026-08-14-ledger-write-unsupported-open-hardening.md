# Sprint Tick Review: `RunLedger.write_jsonl` unsupported-open error hardening

- **Selected slice:** Normalize `NotImplementedError` and `TypeError` from unsupported descriptor-relative `os.open` calls into privacy-safe `ValueError` without masking unrelated serialization `TypeError`.
- **Changed files:** `src/forgecode_agent/ledger.py`, `tests/unit/test_run_ledger.py`.
- **Implementation:** Added a local descriptor-open wrapper that translates only unsupported `os.open` errors to `ValueError("Cannot write JSONL ledger file/path")` with no cause; serialization and write-time `TypeError` remain unchanged. Added parametrized unsupported-open tests and a serialization regression test.
- **TDD evidence:** Unsupported-open tests failed before implementation because `NotImplementedError`/`TypeError` escaped. The serialization regression failed against the broad catch because it was incorrectly normalized. All focused tests passed after narrowing the wrapper.
- **Verification:** Focused ledger tests: 43 passed. Full suite: 323 passed. `python -m compileall -q src tests`: passed. `git diff --check`: passed. Static security scan: no findings. Spec review: PASS. Quality/security review after fix: APPROVED.
- **Build:** `python -m build --wheel --no-isolation -o /tmp/forgecode-wheel-check` unavailable because the `build` module is not installed in this environment; not caused by this slice.
- **Status:** Ready for parent pre-commit review, local commit, and push. No secrets, network calls, subprocesses, or unrelated files included.

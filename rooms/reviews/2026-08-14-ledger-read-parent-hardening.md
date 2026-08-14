# Sprint Tick Review: `RunLedger.read_jsonl` parent-path hardening

- **Selected slice:** Reject symlinked parent directories during JSONL ledger reads without following them, while preserving fail-closed and privacy-safe error behavior.
- **Changed files:** `src/forgecode_agent/ledger.py`, `tests/unit/test_run_ledger.py`.
- **Implementation:** Descriptor-relative parent traversal with `O_NOFOLLOW`/`O_DIRECTORY`, regular-file validation, nonblocking final open, and normalization of unsupported descriptor-relative open errors to `ValueError`. Added regression coverage for symlinked parents and unsupported `os.open` behavior; aligned capability skip guards.
- **TDD evidence:** The symlinked-parent regression failed against the prior path-based reader (`DID NOT RAISE ValueError`). Portability tests for `NotImplementedError`/`TypeError` also failed before normalization. All passed after implementation.
- **Verification:** Focused ledger tests: 40 passed. Full suite: 320 passed. `git diff --check`: passed. `python -m compileall -q src tests`: passed. Static security scan: no findings. Independent spec review: PASS. Independent quality/security review: APPROVED. Independent pre-commit JSON review: `passed=true`.
- **Build:** `python -m build` unavailable because the `build` module is not installed in this environment; not caused by this slice.
- **Status:** Approved for local commit and push. No secrets, network calls, subprocesses, or unrelated files included.

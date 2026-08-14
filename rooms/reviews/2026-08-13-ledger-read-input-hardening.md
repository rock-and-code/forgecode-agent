# Review: RunLedger JSONL input hardening

- **Slice:** Reject symlink and special-file inputs in `RunLedger.read_jsonl` without blocking or following paths.
- **Changed:** `src/forgecode_agent/ledger.py`, `tests/unit/test_run_ledger.py`.
- **Safety:** Descriptor-based `O_NOFOLLOW` + `O_NONBLOCK`, `fstat` regular-file check, privacy-safe `ValueError`; platforms without `O_NOFOLLOW` fail closed and are covered by a test.
- **TDD evidence:** New symlink/FIFO tests were observed failing against the prior path-based reader; implementation then made them pass.
- **Verification:** 34 focused ledger tests passed; full suite 314 passed; `git diff --check` passed. Ruff reports two pre-existing unused-variable findings outside this slice (`src/forgecode_agent/cli.py`, `tests/unit/test_cli_init.py`). Wheel build was unavailable because `build` is not installed.
- **Independent reviews:** Spec compliance PASS. Quality/security re-review PASS; only non-blocking suggestion was portability handling for `O_NONBLOCK`.
- **Status:** Approved for local commit and push. No secrets, network calls, subprocesses, or unrelated files included.

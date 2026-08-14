# Sprint Tick Review: `RunLedger.write_jsonl` output-path hardening

- **Selected slice:** Reject symlinked final outputs, symlinked parent directories, and FIFO/special-file outputs without following, modifying, or blocking on them.
- **Changed files:** `src/forgecode_agent/ledger.py`, `tests/unit/test_run_ledger.py`.
- **Implementation:** Descriptor-relative `O_NOFOLLOW`/`O_DIRECTORY` parent traversal and creation, `O_NONBLOCK` final open, regular-file `fstat`, fail-closed unsupported-platform behavior, privacy-safe `ValueError`.
- **TDD evidence:** New final-output symlink and FIFO tests failed against the prior path-based writer; the parent-symlink regression also failed before the descriptor-relative fix. All passed after implementation.
- **Verification:** Focused ledger tests: 37 passed. Full suite: 317 passed. `git diff --check`: passed. Static security scan: no findings. Independent spec review: PASS. Independent quality/security review: APPROVED. Independent pre-commit JSON review: passed=true.
- **Build:** `python -m build` was checked separately; the `build` module is not installed in this environment, so wheel verification is unavailable (not caused by this slice).
- **Status:** Approved for local commit and push. No secrets, network calls, subprocesses, or unrelated files included.

# Sprint review: doctor config path hardening

- **Slice:** Harden `forgecode doctor` against symlinked `.forge/config.toml`, symlinked `.forge` directories, and blocking special files.
- **Implementation:** Descriptor-relative traversal with `O_NOFOLLOW`; config is read from the already-open descriptor; `O_NONBLOCK` prevents FIFO blocking; non-regular files are reported as missing.
- **Changed files:** `src/forgecode_agent/cli.py`, `tests/unit/test_cli_doctor.py`
- **TDD evidence:** Regression tests were observed failing before each corresponding implementation fix, then passed after the minimal change.
- **Review:** Spec compliance passed. Independent quality review approved after eliminating TOCTOU and symlinked-directory issues. Pre-commit security review flagged FIFO blocking; the issue was fixed with a regression test and `O_NONBLOCK`.
- **Verification:** Focused doctor tests: 15 passed. Full suite: 310 passed. `git diff --check`: clean.
- **Approval boundary:** Local code/test change only; no external user-facing action was taken beyond the requested repository push.

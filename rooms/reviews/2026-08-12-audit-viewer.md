# Sprint review: read-only audit viewer

- Slice: add `forgecode audit` for recent JSONL audit events.
- Scope: `--audit-log` plus positive `--limit` (default 5); read-only, no self-audit.
- Hardening: bounded tail memory, descriptor-relative `O_NOFOLLOW` reads, regular-file validation, FIFO non-blocking open, macOS parent-path canonicalization, and symlink-loop error handling.
- Changed files:
  - `src/forgecode_agent/cli.py`
  - `tests/unit/test_cli_audit.py`
- TDD evidence: focused tests were observed failing before implementation for the command, bounded streaming, symlink safety, parent-path portability, FIFO blocking, and symlink-loop handling; fixes were then implemented incrementally.
- Verification: `python -m pytest -q` → 306 passed; `git diff --check` clean.
- Independent reviews: spec compliance PASS; final security/quality review APPROVED.
- Note: repository-wide Ruff reports two pre-existing F841 findings outside this slice (`cli.py:474` and `tests/unit/test_cli_init.py:207`); no new lint findings attributable to the slice were identified.
- Status: ready for local commit and push.

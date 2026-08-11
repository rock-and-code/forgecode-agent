# Sprint Tick Review: read-only `forgecode config`

Date: 2026-08-11
Slice: B4a — inspect local ForgeCode configuration without mutation.

## Scope delivered

- Added `forgecode config --workspace PATH` with current-directory default.
- Reads `.forge/config.toml` and prints supported quoted string entries sorted by key.
- Reports `config: ok` for readable configs with no supported string entries.
- Reports `config: missing` with exit code 1 for missing, non-regular, unreadable, undecodable, symlinked config files, and symlinked `.forge` directories.
- Uses descriptor-relative, no-follow opens and fails closed when `O_NOFOLLOW` is unavailable to avoid path redirection and TOCTOU reads.
- No config mutation and no changes to existing init/status/doctor behavior.

## TDD and verification

- RED evidence captured for unknown `config` command, symlinked config, descriptor-based reading, symlinked `.forge`, and unavailable `O_NOFOLLOW` cases.
- Focused config tests: 8 passed.
- Full suite: 274 passed.
- `python -m compileall -q src tests`: passed.
- Wheel build via `python -m pip wheel . --no-deps`: passed (`forgecode_agent-0.0.0-py3-none-any.whl`).
- `git diff --check`: passed.
- Static security scan: no hardcoded secrets, shell injection, eval/exec, pickle, or SQL-formatting patterns in the slice.
- Ruff reports one pre-existing unrelated F841 in `tests/unit/test_cli_init.py:190`; no new lint findings were introduced by this slice.

## Independent review gates

- Spec-compliance review after fixes: PASS.
- Code quality/security review after fixes: APPROVED; no critical or important issues.

No secrets, credentials, network calls, or destructive operations were used.

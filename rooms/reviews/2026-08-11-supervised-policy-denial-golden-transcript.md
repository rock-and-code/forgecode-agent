# Sprint Tick Review: supervised policy-denial golden transcript

## Selected slice

Add deterministic golden-transcript coverage for the controller's supervised policy-denial terminal path. The test must prove that a known shell tool requiring approval is denied before its handler runs and that the run stops without requesting another model response.

## Files changed

- `tests/unit/test_agent_controller.py` — adds a timestamp-independent golden transcript regression test and asserts the handler and registry history remain unused.
- `tests/golden/supervised_policy_denial_terminal.json` — records the expected run, model, tool-request, policy-denial, failure, and terminal events.
- `rooms/reviews/2026-08-11-supervised-policy-denial-golden-transcript.md` — records this review artifact and its verification evidence.

## TDD evidence

- RED: focused test failed because `tests/golden/supervised_policy_denial_terminal.json` was absent (`1 failed`).
- GREEN: focused test passed (`1 passed`).

## Review and verification

- Spec-compliance review: PASS.
- Independent quality/security review: APPROVED; no critical or important issues.
- Focused test: `python3 -m pytest -q tests/unit/test_agent_controller.py::test_agent_controller_supervised_policy_denial_matches_golden_transcript` — passed.
- Full suite: `python3 -m pytest -q` — `254 passed`.
- Packaging: `python3 -m pip wheel . --no-deps -w /tmp/forgecode-cron-wheel-check` — succeeded.
- `git diff --check` and JSON parse validation — passed.
- No production code, secrets, network calls, or unrelated files were changed.

## Follow-up

Continue adding golden transcript cases only for important MVP controller branches; otherwise advance to the next documented backlog slice.

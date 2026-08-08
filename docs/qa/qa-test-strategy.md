# ForgeCode Agent QA and Test Strategy

Status: Draft v0.1  
Scope: quality strategy and test architecture only; no application code is defined here.

## 1. Purpose

ForgeCode Agent is a coding agent intended to plan, edit, test, and safely operate on user repositories. The QA strategy must prove that the agent is:

- Correct: produces expected plans, edits, commands, and summaries for well-defined tasks.
- Deterministic where required: reproducible under fixed seeds, fixed model responses, and fixed fixtures.
- Safe: resists prompt injection, path traversal, secret exfiltration, dangerous shell use, and unauthorized workspace changes.
- Observable: emits enough structured events to debug decisions and verify policy enforcement.
- Recoverable: handles tool errors, model errors, interrupted runs, and partially applied changes without corrupting the workspace.
- Maintainable: supports TDD, regression tests, golden transcript review, and future provider/tool expansion.

## 2. Quality principles

1. **Test behavior, not implementation details.** Public interfaces, event streams, tool calls, file-system effects, and final summaries are the main contract.
2. **Determinism by default.** Tests must use fake model providers, fake tools, frozen clocks, seeded randomness, isolated temporary workspaces, and normalized paths.
3. **No network by default.** Unit and most integration tests must run without external APIs. Network-enabled tests are opt-in, marked, rate-limited, and excluded from required CI gates.
4. **Security is a first-class feature.** Abuse tests are not optional regression tests; they are merge blockers for any component that touches prompts, tools, shell, files, git, secrets, or policies.
5. **Golden outputs are reviewed artifacts.** Golden transcripts and expected patches should be human-readable, minimal, normalized, and updated only with explicit review.
6. **Every bug gets a regression test.** A defect is not fixed until a focused failing test exists and then passes.
7. **No product code before test intent.** New behavior starts with a test plan entry, acceptance criteria, fixtures, and at least one failing automated test where practical.

## 3. TDD rules for implementation teams

### Required flow

1. Write or update a test matrix entry for the feature or bug.
2. Add focused acceptance criteria.
3. Create failing tests at the lowest useful level:
   - unit for pure logic;
   - integration for component contracts;
   - e2e/golden for agent loop behavior;
   - security abuse test for risky surfaces.
4. Implement the minimal application code needed to pass.
5. Refactor with tests green.
6. Add or update observability assertions if the behavior affects decision-making, tools, policy, or workspace state.
7. Run the local quality gate before opening a PR.

### Definition of done

A change is done only when:

- All affected automated tests pass.
- New behavior has regression coverage.
- Security-sensitive behavior has explicit negative tests.
- Golden transcript changes are reviewed and intentionally accepted.
- CI is green across supported platforms.
- Documentation or user-facing behavior notes are updated when relevant.

### Forbidden shortcuts

- Do not call real model APIs in required tests.
- Do not require developer-global state, real credentials, or a real user home directory.
- Do not assert against unnormalized absolute paths, wall-clock timestamps, random IDs, or nondeterministic ordering.
- Do not make tests depend on execution order.
- Do not allow tests to write outside their temporary workspace.
- Do not bless a golden transcript change without understanding why it changed.

## 4. Test pyramid

### Unit tests

Goal: fast, deterministic checks of pure or near-pure logic.

Expected coverage areas:

- Prompt assembly and prompt section ordering.
- Policy evaluation and permission decisions.
- Path normalization and workspace boundary checks.
- Command classification and shell safety rules.
- Tool schema validation and argument parsing.
- Diff/patch parsing and application planning.
- Context window accounting and compaction triggers.
- Transcript/event serialization.
- Retry/backoff state machines with fake clocks.
- Error normalization and user-facing error categories.

Target runtime: under 5 seconds for the full unit suite during early development; under 30 seconds as the project grows.

### Integration tests

Goal: verify contracts between real components with fake external dependencies.

Expected coverage areas:

- Agent loop with fake model provider and fake tool registry.
- Workspace file adapter against temporary repositories.
- Git/worktree adapter against real local git repositories in temp directories.
- Sandbox command runner with constrained commands and fake or real isolated process execution.
- Context manager with realistic transcript and source fixtures.
- Policy engine + tool execution boundary.
- Event logger + transcript recorder + redaction layer.

Target runtime: under 2 minutes for required integration tests.

### End-to-end tests

Goal: run the full agent stack against temporary repositories using fake providers and controlled fixtures.

Expected coverage areas:

- Simple edit task.
- Multi-file refactor task.
- Test-fix loop where first command fails and second succeeds.
- Clarification-required task where missing context blocks execution.
- Tool failure recovery.
- Security refusal or safe alternative behavior.
- Git branch/worktree workflow.
- Context compaction during long task.

Required e2e tests must not call real model APIs or external networks. Optional live-provider smoke tests may exist separately and must be excluded from normal CI.

### Golden transcript tests

Goal: lock down high-value agent behaviors as readable conversations and event traces.

Golden artifacts should include:

- user request;
- system/developer policy fixtures;
- fake model response script;
- expected tool calls;
- expected normalized file diffs;
- expected event stream;
- final user response;
- expected safety decisions.

Golden tests should compare normalized structures, not raw incidental formatting. Use stable IDs, frozen times, sorted keys, and path placeholders such as `<WORKSPACE>`.

### Property-based tests

Goal: discover edge cases in input validation, parsers, path handling, patch handling, and compaction logic.

Candidate properties:

- Path normalization never escapes workspace for allowed relative paths.
- Rejected path traversal patterns are always rejected.
- Diff parser either produces a valid patch model or a categorized error; never crashes.
- Context compaction preserves required system/developer/security constraints.
- Command classifier is conservative for unknown shell syntax.
- Redaction is idempotent and never reveals known secret patterns after repeated serialization.

### Mutation testing

Goal: measure whether tests actually catch behavior changes.

Initial mutation targets:

- Policy allow/deny branches.
- Workspace boundary comparisons.
- Secret redaction regexes.
- Retry limits and loop termination conditions.
- Context budget threshold comparisons.
- Tool schema required fields.

Mutation testing can begin as a nightly or manual gate and later move into scheduled CI.

## 5. Core quality risks and required mitigations

- **Prompt injection succeeds through repository files.** Mitigate with hostile fixture repos, source attribution, instruction hierarchy tests, and assertions that untrusted content cannot override system/developer policy.
- **Agent runs dangerous shell commands.** Mitigate with command classification tests, sandbox integration tests, allowlist/denylist tests, and explicit user-confirmation simulation.
- **Path traversal modifies files outside workspace.** Mitigate with property tests and real temp-directory boundary tests involving symlinks, `..`, absolute paths, Unicode, and case sensitivity.
- **Secrets are leaked into prompts, logs, commands, or final answers.** Mitigate with secret fixture files, redaction assertions, transcript checks, and abuse prompts requesting exfiltration.
- **Nondeterminism makes failures unreproducible.** Mitigate with fake providers, frozen clocks, deterministic ordering, seeded randomness, and snapshot normalization.
- **Context compaction loses critical constraints.** Mitigate with long-transcript fixtures and invariant assertions that policy, user goal, safety constraints, open tasks, and file state survive compaction.
- **Git/worktree corruption.** Mitigate with isolated real-git tests checking branch state, dirty state detection, untracked files, rollback behavior, and no accidental commits.
- **Infinite or wasteful loops.** Mitigate with deterministic loop budgets, fake model scripts, max-iteration tests, and clear terminal states.

## 6. Test matrix

### Agent loop and planning

- Unit: plan state transitions, loop budget checks, terminal state classification.
- Integration: fake model emits scripted tool calls; agent executes or refuses according to policy.
- E2E/golden: deterministic transcript for plan-edit-test-summarize flow.
- Security: hostile model asks to ignore policies or hide actions; agent must refuse or constrain.

### Model provider abstraction

- Unit: request serialization, response parsing, token accounting, retry decisions.
- Integration: fake provider scripts streaming, tool calls, malformed responses, rate limits, and timeouts.
- E2E/golden: full run with scripted provider.
- Security: provider output attempts prompt injection, secret requests, or unauthorized tool use.

### Tool system

- Unit: schema validation, argument coercion rejection, permission labels.
- Integration: fake tools verify call order, idempotency, error propagation.
- E2E/golden: tool failure recovery and final summary.
- Security: malicious tool output tries to become instructions.

### File editing and patching

- Unit: path checks, diff parsing, conflict detection, binary-file refusal rules.
- Integration: edits in temp workspace, rollback on failure, preserve file modes where required.
- E2E/golden: expected patch for multi-file change.
- Security: path traversal, symlink escape, hidden files, secrets, generated/binary files.

### Sandbox and shell

- Unit: command classifier, risk labels, timeout handling, environment filtering.
- Integration: command runner in temp workspace with no inherited secrets and bounded resources.
- E2E/golden: test command failure then repair loop.
- Security: destructive commands, network commands, curl pipe shell, credential printing, fork bombs, background daemons.

### Git and worktrees

- Unit: parse status, branch naming, dirty-state policy.
- Integration: real local git repo fixtures for branch creation, worktree creation, diff extraction, revert, conflict handling.
- E2E/golden: agent works on branch/worktree and reports diff without committing unless requested.
- Security: malicious git hooks, submodules, ignored files, pathspec injection.

### Context and memory

- Unit: token counting, chunk ranking, compaction invariants.
- Integration: long transcript compaction with file summaries and task state.
- E2E/golden: long task crosses budget and still completes correctly.
- Security: injected instructions in summarized context must remain labeled as untrusted.

### Observability and transcripts

- Unit: event schema, redaction, stable serialization.
- Integration: event stream aligns with executed actions and policy decisions.
- E2E/golden: transcript contains enough detail to reproduce behavior.
- Security: logs redact secrets and do not include hidden prompts beyond allowed debug modes.

## 7. Fake model provider requirements

The fake model provider is the foundation for deterministic tests. It should support:

- Scripted responses by turn number, prompt matcher, or state predicate.
- Tool-call responses and normal text responses.
- Streaming and non-streaming modes.
- Malformed outputs for parser tests.
- Simulated provider errors: timeout, rate limit, overload, invalid API key, truncated response.
- Token usage reporting with configurable budgets.
- Deterministic IDs and timestamps.
- Assertions that prompts include or exclude required sections.
- Assertions that secrets and disallowed files are not sent to the model.

Provider scripts should be stored as fixtures, not embedded deeply in test bodies when they become large.

## 8. Fake tools requirements

Fake tools should allow tests to verify agent behavior without touching real systems.

Capabilities:

- Register named tools with schemas, permissions, and risk levels.
- Return scripted success, failure, timeout, or malformed results.
- Record calls with normalized arguments.
- Assert call order or allow unordered call sets where order is irrelevant.
- Simulate untrusted output that contains prompt injection attempts.
- Simulate partial failure and retry behavior.
- Enforce workspace boundary checks even in fake mode.

Use real local adapters only when the contract being tested requires actual filesystem, git, or process behavior.

## 9. Sandbox test requirements

Sandbox tests must prove that command execution is constrained.

Required scenarios:

- Commands execute with current directory set to temporary workspace.
- Environment excludes host secrets by default.
- Command timeout terminates process and reports a categorized error.
- Output size limits truncate safely with clear markers.
- Attempts to read outside workspace are blocked or require explicit permission.
- Attempts to write outside workspace are blocked.
- Dangerous shell syntax is refused or gated.
- Network access defaults to off for required tests.
- Background processes are cleaned up after tests.
- Symlink escape attempts fail.

## 10. Git/worktree test requirements

Use real git in temporary directories for integration tests because git behavior is complex and platform-sensitive.

Required scenarios:

- Detect clean, dirty, staged, untracked, conflicted, and detached HEAD states.
- Create a feature branch from a clean working tree.
- Create and remove an isolated worktree.
- Refuse or ask before overwriting user changes.
- Preserve untracked user files.
- Generate normalized diffs for final summaries.
- Handle merge conflicts as recoverable errors.
- Disable or ignore repository hooks during tests unless hooks are explicitly under test.
- Prevent pathspec injection through filenames beginning with `-` or containing unusual characters.

## 11. Context compaction test requirements

Compaction must be tested as a safety-critical behavior.

Required invariants:

- System/developer rules are never dropped or weakened.
- User goal and explicit constraints are preserved.
- Current plan, completed steps, pending steps, and known failures are preserved.
- Files changed and command outputs relevant to decisions are preserved.
- Untrusted source content remains labeled as untrusted.
- Secrets remain redacted.
- Compaction output is deterministic for the same input.
- Agent can continue after compaction and make the same next decision as before compaction when given equivalent state.

## 12. Security abuse suite

Security tests are merge-blocking for affected components.

### Prompt injection

- Repository README instructs agent to ignore system rules.
- Test output contains malicious instructions.
- Tool output says to exfiltrate secrets.
- Dependency documentation includes fake higher-priority instructions.
- Hidden comments in source files attempt to change behavior.

Expected result: agent treats content as data, preserves instruction hierarchy, and refuses unsafe requests.

### Shell abuse

- Request to run destructive commands such as `rm -rf`, disk wipe patterns, credential dumping, or process killing outside scope.
- Command substitution hides dangerous behavior.
- Curl/wget pipe-to-shell pattern.
- Fork bomb or resource exhaustion pattern.
- Background daemon that persists after the run.

Expected result: refuse, require confirmation, or run only in constrained sandbox according to risk policy.

### Path traversal and filesystem abuse

- `../` escape attempts.
- Absolute path writes outside workspace.
- Symlink escape.
- Unicode confusables and normalized path tricks.
- Case-insensitive filesystem collisions.
- Filenames beginning with dash or containing newlines.

Expected result: no writes outside workspace and clear safety error.

### Secrets

- `.env`, private keys, npm tokens, cloud credentials, SSH keys, and API-key-like strings in fixtures.
- User asks agent to print or summarize secrets.
- Malicious tests ask agent to send secrets to provider or shell.
- Logs and transcripts are checked for redaction.

Expected result: secrets are not exposed unless an explicit, safe, user-authorized workflow is implemented and tested.

## 13. CI gates

### Required on every PR

- Formatting check.
- Lint/static analysis.
- Type check where applicable.
- Unit tests.
- Integration tests using fake model provider and local temp workspaces.
- Required e2e/golden transcript tests.
- Required security abuse tests.
- Coverage report with configured minimum once product code exists.
- Artifact upload for failing transcripts, logs, and diffs with secrets redacted.

### Scheduled or optional gates

- Mutation testing.
- Property-based extended runs.
- Cross-platform matrix: macOS, Linux, Windows.
- Live-provider smoke tests with strict budgets and non-secret fixtures.
- Performance regression tests for large repositories and long transcripts.
- Dependency vulnerability scan.

### Merge-blocking policy

No PR can merge if it weakens safety tests, removes golden coverage without replacement, or changes expected safety behavior without explicit review.

## 14. Test data and fixture governance

- Fixtures must not contain real secrets.
- Use generated fake secrets with recognizable patterns for redaction tests.
- Fixture repositories should be small, focused, and named by behavior.
- Large generated fixtures should be reproducible from documented generation scripts once code exists.
- Golden transcripts require review and should be easy to diff.
- Prefer normalized JSON/YAML for structured fixtures.

## 15. Reporting and observability expectations

Tests should verify that the agent emits structured events for:

- model request and response metadata, with sensitive content controlled;
- tool call requested, allowed/denied, started, completed, failed;
- policy decision and reason;
- file read/write/patch summary;
- shell command risk classification;
- context compaction start/end and preserved invariants;
- git/worktree operation;
- final summary and unresolved issues.

These events make deterministic assertions possible and support debugging failed golden tests.

## 16. Initial acceptance criteria for QA readiness

Before product implementation begins, the repository should contain:

- QA strategy document.
- Initial test suite design document.
- Test matrix with planned coverage areas.
- Fixture layout proposal.
- Golden transcript format proposal.
- Security abuse scenarios.
- CI gate plan.

This document and `initial-test-suite-design.md` satisfy the documentation portion of that readiness checklist.

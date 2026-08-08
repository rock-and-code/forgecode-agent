# ForgeCode Agent Architecture Research

Status: design draft for review  
Scope: open-source coding agent in the same broad category as Claude Code, Codex CLI, OpenCode, Aider, and SWE-agent. This document is intentionally architectural only; no application/source code is included.

## 1. Executive summary

**ForgeCode Agent** is a proposed local-first, open-source coding agent for repository understanding, planning, editing, testing, and review. It should feel like a senior pair-programmer that can operate interactively from a CLI/TUI, delegate bounded work to specialized subagents, execute tools through policy-controlled sandboxes, and produce concise, auditable code changes.

The design avoids copying proprietary product behavior. It borrows only category-level ideas common to coding agents: conversational coding, repository indexing, tool use, patch generation, tests, git isolation, and agentic repair loops.

Recommended positioning:

- **Working name:** ForgeCode Agent is descriptive and serviceable.
- **Possible shorter OSS name:** `forge-agent` or `codeforge` if package-name availability matters.
- **Core differentiator:** a transparent multi-agent workbench with explicit contracts, resumable execution traces, and strict patch/test gates rather than an opaque autonomous black box.

## 2. Reference landscape

The agent should learn from existing public patterns without cloning any single tool.

### Claude Code / Codex-style capabilities

Category capabilities to support:

- Natural-language task intake against a local repository.
- Repo exploration using search, file reads, language-aware symbols, and dependency metadata.
- Plan generation before edits for non-trivial tasks.
- Tool execution for shell commands, tests, formatters, linters, and package managers.
- Patch-oriented file edits with diffs visible to users.
- Git-aware workflows: branches, worktrees, checkpoints, revert, commit messages.
- Configurable approval modes for reads, writes, shell commands, network, and destructive actions.
- Session continuity through summaries, traces, and repository memory.

### Aider-style lessons

- Strong git integration and diff-centric workflows create trust.
- Users need precise control over which files are in context.
- Patch review and commit creation should be first-class.
- LLM output should be constrained to small, understandable edits.

### SWE-agent-style lessons

- Explicit agent loops work well for issue-to-patch automation.
- Test feedback should drive iterative repair.
- Reproducibility matters: capture commands, outputs, environment, and patch state.
- Long-running automation needs a budget, stop conditions, and diagnostics.

### OpenCode-style lessons

- Provider/model abstraction is essential for OSS adoption.
- Terminal-native UX with optional TUI makes the tool portable.
- Extensible tool registries and local configuration avoid hard-coded workflows.

## 3. Design goals and non-goals

### Goals

- **Local-first and transparent:** repository data stays local unless a configured model provider receives selected prompt context.
- **Implementation-ready modularity:** components have narrow interfaces and can be tested independently.
- **Concise code generation:** prefer minimal patches, small functions, simple abstractions, and existing project style.
- **Safe autonomy:** subagents can work independently only within explicit budgets and permissions.
- **Reviewability:** every edit has a rationale, diff, tool trace, and verification status.
- **Provider-neutral:** support multiple LLM APIs and local models through a common interface.
- **Plugin-friendly:** tools, subagents, context providers, UI commands, and policy rules are extensible.

### Non-goals for the first implementation

- Full IDE replacement.
- Background daemon that changes code without explicit user/session authorization.
- Arbitrary browser automation.
- Proprietary protocol compatibility.
- Training or fine-tuning models as part of the core product.

## 4. Proposed architecture overview

ForgeCode is split into thin interfaces around a central orchestrator. The CLI/TUI never directly edits files or runs commands; it sends intents to the session controller. The controller owns policy decisions and invokes the agent runtime. The runtime coordinates context retrieval, planning, tool calls, subagents, patch application, verification, and trace persistence.

Primary layers:

1. **Presentation:** CLI, TUI, optional machine-readable JSON mode.
2. **Session/application:** command parsing, session state, approvals, human-in-the-loop prompts.
3. **Agent runtime:** loop engine, planner, context builder, subagent coordinator, tool router.
4. **Domain services:** repository map, patch manager, git/worktree manager, memory service, policy engine.
5. **Infrastructure:** model providers, sandbox executor, filesystem adapter, embeddings/vector store, logs/traces.

## 5. Core modules

### CLI and TUI boundaries

The CLI should be scriptable and stable. The TUI should be optional and depend on the CLI/application layer rather than the reverse.

- **CLI responsibilities**
  - Parse flags and commands.
  - Start or resume sessions.
  - Print plans, diffs, tool output, and final summaries.
  - Provide JSON output for automation.
  - Never directly mutate repository state except through application services.

- **TUI responsibilities**
  - Display conversation, plan, file context, diffs, command output, and token/budget status.
  - Provide approval dialogs and keyboard shortcuts.
  - Subscribe to runtime events.
  - Reuse the same session API as the CLI.

Boundary rule: `ui -> application -> domain/runtime -> infrastructure`. No domain object should import terminal UI code.

### Agent runtime

The runtime implements a bounded observe-plan-act-verify loop.

Loop phases:

1. **Intake:** normalize user request, repository root, current git state, configured permissions.
2. **Classify:** decide task type: explain, inspect, edit, test, refactor, debug, review, commit.
3. **Context build:** retrieve relevant files, symbols, dependency metadata, prior session summaries, and user-provided constraints.
4. **Plan:** produce a short plan with target files, tools, risks, and verification steps.
5. **Approval gate:** ask only when policy requires it; otherwise continue.
6. **Act:** read, search, edit via patch manager, run tools through sandbox executor.
7. **Verify:** run targeted tests/linters/type checks; inspect diffs.
8. **Repair:** if verification fails and budget remains, update context and retry.
9. **Summarize:** report changes, verification, risks, and suggested next steps.
10. **Persist:** store trace, memory candidates, and git checkpoint metadata.

### Subagent orchestration

Subagents are specialized workers with strict contracts, not unconstrained chatbots. They receive a task packet and return structured findings or patches.

Recommended built-in subagents:

- **Scout:** repository exploration, file discovery, dependency mapping.
- **Architect:** implementation plan, boundaries, design risks.
- **Editor:** minimal patch creation in selected files.
- **Verifier:** test/diagnostic command selection and result interpretation.
- **Reviewer:** diff review for correctness, style, security, and regressions.
- **Documenter:** docs/comments/changelog updates when requested.

Subagent rules:

- Each subagent has an explicit role prompt, tool allowlist, max turns, token budget, and output schema.
- The coordinator owns final decisions; subagents propose, not commit.
- Parallel subagents may inspect context concurrently, but write-capable subagents must operate on isolated patch branches or patch proposals.
- Merge conflicts between subagent patches are resolved by the coordinator, then reviewed.

### Tool execution sandbox

Tool execution should be mediated by a sandbox service with policy checks, environment controls, and durable logs.

Capabilities:

- Read-only commands for discovery.
- Write commands for generated files, formatters, package managers, build artifacts.
- Network access toggle.
- Destructive command detection and approval.
- Timeout, output limits, and process cancellation.
- Environment variable redaction.
- Command provenance: who requested it, why, cwd, env diff, exit code, stdout/stderr digest.

Sandbox levels:

- **Level 0: No shell.** File reads/search only.
- **Level 1: Read-only shell.** Commands must not mutate working tree.
- **Level 2: Workspace write.** Mutations allowed under repo root.
- **Level 3: Network/package access.** Explicit approval or trusted config.
- **Level 4: Elevated/destructive.** Always interactive approval; disabled in unattended mode.

Implementation options to evaluate:

- Native local process runner with policy guardrails for MVP.
- Containerized executor for stronger isolation on Linux.
- macOS sandbox profiles where practical.
- Future remote execution adapter for CI-like environments.

### Git and worktree strategy

Git is central to safety and review.

Recommended strategy:

- Refuse autonomous edit sessions when the repository is not inside git unless user accepts a temporary snapshot mode.
- Capture initial state: branch, HEAD, dirty files, ignored files policy.
- Create a checkpoint before edits.
- Prefer **git worktrees** for long-running autonomous tasks or parallel subagents.
- For interactive tasks, edit the current working tree only after showing planned files and receiving policy approval.
- Store patch proposals as unified diffs before applying.
- Support `review`, `revert`, `commit`, and `export patch` commands.

Worktree modes:

- **Inline mode:** small, interactive patches applied in current tree.
- **Scratch worktree mode:** agent edits an isolated worktree and presents a diff back to the main tree.
- **Subagent branch mode:** each write-capable subagent works on a temporary branch/worktree; coordinator cherry-picks or reapplies selected diffs.

Dirty-tree policy:

- Never overwrite user changes silently.
- Detect changed files before each patch apply.
- If a target file changed externally, pause, re-read, and rebase the patch.

### Context and memory model

Context should be explicit, layered, and inspectable.

Context layers:

1. **Immediate user request:** current message, selected files, command flags.
2. **Repository state:** file tree, git status, language/package metadata.
3. **Retrieved code context:** relevant files/snippets/symbols/tests.
4. **Execution context:** tool outputs, test failures, patch diffs.
5. **Session memory:** concise rolling summary and decisions.
6. **Project memory:** opt-in facts about architecture, commands, style, and conventions.
7. **User/global preferences:** opt-in style and workflow preferences.

Memory rules:

- Store project memory in a visible repo-local file or local metadata directory; never hide critical behavior.
- Separate durable memories from ephemeral session summaries.
- Ask before storing sensitive or cross-project information.
- Include provenance and timestamps for memory entries.
- Allow users to list, edit, disable, or delete memories.

Retrieval approach:

- Start with fast lexical search and file graph heuristics.
- Add tree-sitter or language-server symbol extraction for code navigation.
- Optional embeddings for large repositories.
- Rank context by task relevance, recency, imports/call graph proximity, and test linkage.

### Security model

Threat model:

- Prompt injection in repository files, docs, comments, issue text, test output, logs, or web content.
- Malicious package scripts or commands.
- Exfiltration of secrets through model prompts or network commands.
- Destructive filesystem operations.
- Supply-chain risks from plugins.

Controls:

- Treat repository content and tool output as untrusted data, never instructions.
- Maintain a system/developer policy layer that cannot be overridden by project text.
- Redact secrets before sending context to model providers.
- Provide model-provider data disclosure warnings and configuration.
- Require approval for network, package install, credential access, shell scripts, and destructive commands.
- Sign or checksum plugins where possible; load only from trusted locations by default.
- Sandboxed plugin permissions: filesystem scopes, command scopes, network scopes.
- Audit log for all tool calls and model requests, with sensitive fields redacted.

### Extension and plugin architecture

Plugins should extend capability without weakening safety.

Extension points:

- **Tools:** new callable operations with schemas and permission metadata.
- **Context providers:** framework-specific retrieval, docs, API specs.
- **Subagents:** specialized roles with tool policies and output schemas.
- **Model providers:** adapters for hosted and local LLMs.
- **Policy rules:** organization-specific approval and sandbox policies.
- **UI commands:** CLI/TUI commands that call application services.
- **Verification recipes:** project/test-framework-specific commands.

Plugin manifest fields:

- Name, version, license, homepage.
- Entry point and supported ForgeCode API version.
- Permissions requested.
- Tools/subagents/context providers contributed.
- Configuration schema.
- Trust level and signature/checksum metadata.

Design rule: plugins cannot call arbitrary internal services. They receive a narrow capability object based on declared permissions.

### Observability and logging

Observability is required for debugging and trust.

Event stream:

- Session started/resumed/ended.
- Model request started/completed/failed, token counts, provider, latency.
- Tool call requested/approved/denied/started/completed.
- Patch proposed/applied/rejected/reverted.
- Test command result and parsed diagnostics.
- Subagent lifecycle events.
- Policy decisions.

Storage:

- Human-readable session transcript.
- Structured JSONL event log.
- Patch artifacts.
- Optional OpenTelemetry exporter for advanced users.

Privacy:

- Redact secrets from logs by default.
- Allow local-only logs with opt-in telemetry.
- No cloud telemetry by default for an OSS tool.

## 6. Clean code design patterns

Recommended patterns:

- **Hexagonal architecture / ports and adapters:** core domain depends on interfaces, not concrete model/shell/filesystem implementations.
- **Command pattern:** user actions and tool calls represented as auditable commands.
- **Strategy pattern:** model providers, retrieval rankers, sandbox backends, and diff algorithms are swappable.
- **State machine:** agent loop states are explicit and testable.
- **Unit of Work:** patch application, git checkpointing, and verification are grouped into reversible transactions where possible.
- **Repository pattern:** project memory, traces, and config persistence behind interfaces.
- **Policy as data:** permissions and approvals are declarative and testable.
- **Event sourcing lite:** append-only session events reconstruct what happened.
- **Dependency inversion:** UI and infrastructure depend inward on application/domain contracts.

Concise generation rules:

- Minimize changed files and changed lines.
- Prefer existing project idioms over introducing new frameworks.
- Avoid speculative abstractions.
- Keep generated functions small and named for intent.
- Include tests only when valuable and consistent with project style.
- Avoid drive-by formatting outside touched regions unless explicitly requested.

## 7. Suggested package/module boundaries

Language is not mandated by this document. If implemented in TypeScript, Rust, Python, or Go, preserve these logical boundaries.

- `cli`: argument parsing, command output, shell completion.
- `tui`: optional terminal UI views and event subscriptions.
- `app`: sessions, use cases, approvals, orchestration facade.
- `agent`: loop engine, planner, coordinator, subagent runtime.
- `domain`: task, plan, policy, patch, memory, trace, repository abstractions.
- `tools`: built-in tools and schemas.
- `sandbox`: process execution and filesystem policy enforcement.
- `git`: worktree/checkpoint/diff operations.
- `context`: repo map, retrieval, symbol index, embedding adapter.
- `models`: provider interface, prompt assembly, token accounting.
- `plugins`: manifest loader, registry, permission-scoped capabilities.
- `observability`: event bus, logs, traces, redaction.
- `config`: layered config: defaults, user, repo, environment, flags.

## 8. Agent loop details

The loop should be deterministic around state transitions even though model output is probabilistic.

State machine:

- `Idle`
- `Intaking`
- `BuildingContext`
- `Planning`
- `AwaitingApproval`
- `ExecutingTool`
- `ApplyingPatch`
- `Verifying`
- `Repairing`
- `Summarizing`
- `Completed`
- `Failed`
- `Cancelled`

Stop conditions:

- User cancels.
- Plan complete and verification passes.
- Budget exhausted: turns, tokens, wall-clock, command count, or cost.
- Repeated failure signature detected.
- Policy denial blocks required action.
- Unsafe or ambiguous state detected.

## 9. Human-in-the-loop approval model

Approval should be predictable and configurable.

Modes:

- **Ask:** default for writes, shell commands, network, package installs.
- **Auto-read:** allow reads/search/status without prompting.
- **Auto-edit:** allow patch writes under repo root, but still ask for shell/network/destructive commands.
- **Trusted project:** apply repo policy for trusted local projects.
- **Unattended:** only non-interactive safe actions; fail instead of asking.

Approval prompts must show:

- Proposed action.
- Reason.
- Scope: files, cwd, command, network domain, env changes.
- Risk level.
- Alternatives if denied.

## 10. License and open-source considerations

Recommended licenses:

- **Apache-2.0:** permissive, patent grant, common for developer tools.
- **MIT:** simpler permissive license, less explicit patent protection.
- **MPL-2.0:** file-level copyleft if the project wants improvements to core files shared back while allowing proprietary plugins.

Recommended default: **Apache-2.0** for broad adoption and patent clarity.

Considerations:

- Avoid copying prompts, UI text, protocol details, or implementation behavior from proprietary agents.
- Audit dependencies for compatible licenses.
- Define plugin license expectations but do not require all plugins to use the core license unless desired.
- Add a contributor license policy only if the project expects large external contributions.
- Document model-provider terms and data handling separately from the software license.

## 11. Implementation roadmap

### Milestone 0: architecture and prototypes

- Finalize architecture and diagrams.
- Choose implementation language and CLI framework.
- Define domain interfaces and event schemas.
- Build a non-mutating repo inspector prototype separately after review.

### Milestone 1: local interactive MVP

- CLI chat/session shell.
- Model provider interface with one hosted and one local-compatible adapter.
- Read/search tools.
- Context builder with repo map and lexical retrieval.
- Plan generation.
- Structured event log.

### Milestone 2: safe edits

- Patch proposal and application.
- Git checkpointing.
- Approval policy engine.
- Diff review command.
- Formatter/test command execution through sandbox.

### Milestone 3: autonomous repair loop

- Verify/repair cycle.
- Test diagnostics parser.
- Budget enforcement.
- Session resume.
- Project memory.

### Milestone 4: subagents and worktrees

- Scout, Editor, Verifier, Reviewer subagents.
- Scratch worktree mode.
- Parallel read-only exploration.
- Patch merge/review pipeline.

### Milestone 5: plugin ecosystem

- Plugin manifest and registry.
- Permission-scoped plugin APIs.
- Custom tools/context providers/subagents.
- Documentation and examples.

## 12. Key risks and mitigations

- **Risk:** agent makes broad, low-quality edits.  
  **Mitigation:** minimal patch policy, plan gate, diff review, touched-region formatting.

- **Risk:** unsafe command execution.  
  **Mitigation:** sandbox levels, approvals, destructive command detection, timeouts.

- **Risk:** prompt injection from repo content.  
  **Mitigation:** untrusted-content labeling, instruction hierarchy, tool policy enforcement outside the model.

- **Risk:** context bloat and hallucinated understanding.  
  **Mitigation:** retrieval provenance, citations to file paths/line ranges, verification commands.

- **Risk:** plugin supply-chain compromise.  
  **Mitigation:** manifests, permissions, trusted paths, signatures/checksums, disabled-by-default network.

- **Risk:** model-provider lock-in.  
  **Mitigation:** provider-neutral interface and local-model adapter.

## 13. Review checklist before coding

- Confirm project name and license.
- Choose implementation language and packaging target.
- Decide initial model providers.
- Decide default approval mode.
- Define event schema and config schema.
- Define plugin API stability policy.
- Decide whether worktree mode is MVP or post-MVP.
- Document privacy/data handling promises.

## 14. Related diagrams

See:

- `docs/diagrams/forgecode-domain-context.mmd`
- `docs/diagrams/forgecode-agent-flow.mmd`
- `docs/diagrams/forgecode-sequence.mmd`

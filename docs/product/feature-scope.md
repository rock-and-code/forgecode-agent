# ForgeCode Agent Product Scope

Status: Draft v0.1  
Audience: maintainers, product owner, lead developer agents, implementation subagents, QA, documentation contributors  
Scope: product definition, MVP, roadmap, and implementation backlog only. No application/source code is included in this document.

## 1. Product Positioning

ForgeCode Agent is an open-source, docs-first coding agent for software teams and individual developers who want Claude Code/Codex-style terminal assistance with transparent workflows, auditable actions, and controlled autonomy.

The product emphasizes:

- Supervised planning before implementation.
- Source-grounded, documentation-first reasoning.
- Human approval gates for risky changes.
- Autonomous subagent execution after scope is approved.
- Explicit roles for product, lead development, implementation, testing, QA, and documentation.
- Reproducible task logs and project memory suitable for open-source collaboration.

ForgeCode should feel like a trustworthy development teammate rather than an opaque code generator.

## 2. Product Goals

- Provide a local-first CLI coding agent that can inspect repositories, plan work, edit files, run commands, test changes, and summarize results.
- Support a supervised docs-first workflow where requirements and implementation plans are written before code changes begin.
- Enable role-based autonomous loops using specialized subagents.
- Maintain high visibility into actions, tool usage, approvals, risks, and outcomes.
- Be model-provider agnostic where practical, allowing users to configure supported LLM backends.
- Be simple enough for solo developers while structured enough for team workflows.

## 3. Non-Goals

ForgeCode Agent will not attempt to be all of the following in the MVP:

- A full IDE or replacement for VS Code, JetBrains, Cursor, or Zed.
- A hosted SaaS coding platform.
- A browser-based cloud development environment.
- A generalized business automation agent unrelated to software development.
- A fully unsupervised production deployment system.
- A security scanner with compliance guarantees.
- A proprietary model provider or model training platform.
- A multi-user project management suite.

## 4. Target Users

### Primary Users

- Solo developers who want an open-source CLI alternative to commercial coding agents.
- Open-source maintainers who want auditable AI-assisted contributions.
- Small teams that want structured AI implementation workflows without adopting a hosted platform.
- AI tooling researchers experimenting with coding-agent architectures.

### Secondary Users

- Documentation maintainers who want help keeping docs aligned with code.
- QA engineers who want AI-generated test plans and verification checklists.
- Technical product owners who want requirements converted into implementation-ready tasks.
- DevOps engineers who want controlled repository automation without automatic deployment.

## 5. Core Personas

### Product Owner

- Defines desired outcomes, acceptance criteria, constraints, and release priorities.
- Reviews plans before implementation begins.
- Approves scope changes and risky actions.

### Lead Developer Agent

- Converts user requests into technical plans.
- Assigns work to subagents.
- Enforces architecture, quality, and repository conventions.
- Reviews implementation outputs before final handoff.

### Implementer Agent

- Makes focused code or documentation changes for a bounded task.
- Avoids unrelated refactors.
- Reports changed files, reasoning, and verification steps.

### Test Agent

- Runs existing tests.
- Adds or updates tests when in scope.
- Reports failures, regressions, and coverage gaps.

### QA Agent

- Validates acceptance criteria.
- Performs edge-case and behavior review.
- Produces final go/no-go findings.

### Documentation/Manual Developer Agent

- Creates and updates user-facing docs, internal design notes, and release notes.
- Ensures commands, examples, and workflows match implemented behavior.

### Human Maintainer

- Owns final decisions.
- Approves file writes, shell commands, dependency installs, destructive actions, external network use, and publishing.

## 6. MVP Feature List

The MVP should prove the end-to-end loop: understand repository context, draft docs-first plan, get approval, execute bounded changes, test, QA, and summarize.

### 6.1 CLI Foundation

- `forge init`: initialize ForgeCode metadata in a repository.
- `forge status`: show workspace state, active task, configured model provider, and approval mode.
- `forge ask <prompt>`: answer questions about the repository without making changes.
- `forge plan <prompt>`: create an implementation plan and acceptance criteria without editing source files.
- `forge run <task-file|prompt>`: execute an approved task using the autonomous loop.
- `forge review`: review local changes and produce findings.
- `forge test`: run configured validation commands and summarize results.
- `forge docs`: generate or update documentation for approved changes.
- `forge config`: view and update local ForgeCode configuration.

### 6.2 Repository Context Engine

- Read project files with ignore rules respecting `.gitignore` and ForgeCode excludes.
- Produce repository summaries: languages, frameworks, package managers, test commands, build commands, important files.
- Search files by name and content.
- Maintain scoped context bundles for each task.
- Avoid reading secrets by default using configurable deny patterns.

### 6.3 Docs-First Planning

- Generate a task brief before implementation.
- Include problem statement, assumptions, constraints, affected areas, acceptance criteria, risks, test plan, and rollback notes.
- Save plans under a configurable directory, defaulting to `.forge/tasks/`.
- Require human approval before implementation in supervised mode.

### 6.4 Role-Based Autonomous Loop

Minimum supported loop:

1. Product owner/request intake.
2. Lead developer analysis and plan refinement.
3. Human approval gate.
4. Implementer executes a bounded task.
5. Test agent runs verification.
6. QA agent validates acceptance criteria.
7. Documentation agent updates docs if required.
8. Lead developer produces final summary.

### 6.5 Tool Execution and Safety

- File read/write tools with diff preview.
- Shell command execution with approval policies.
- Configurable allowlist/denylist for commands.
- Dry-run mode for plans and reviews.
- Confirmation before destructive operations.
- Audit log of commands, file writes, model calls, approvals, and results.

### 6.6 Model Provider Abstraction

- Support one provider in MVP with a clean interface for additional providers.
- Configuration via environment variables and local config file.
- Provider capability metadata: context size, tool support, streaming support, cost hints if available.
- Clear errors for missing API keys or unsupported provider features.

### 6.7 Task State and Memory

- Store task state locally.
- Track active task, plan, approvals, changed files, test results, and final summary.
- Keep project memory limited to explicit notes and generated repository summaries.
- Allow users to inspect and clear memory.

### 6.8 Review and Reporting

- Summarize changes by file and purpose.
- Include tests run, pass/fail status, unresolved issues, and recommended next steps.
- Produce machine-readable task metadata for future automation.

## 7. Out-of-Scope / Anti-Scope-Creep List

Do not include in MVP unless explicitly reprioritized:

- Cloud-hosted orchestration service.
- Web dashboard.
- Multi-user auth, teams, billing, or permissions.
- Plugin marketplace.
- Pull request bot integration.
- Automatic deployment to production.
- Fine-tuning models.
- Native IDE extensions.
- Full sandbox/VM isolation beyond command approvals and local policy controls.
- Voice interface.
- Long-term autonomous background daemon.
- Enterprise compliance reporting.
- Secret management beyond detection/avoidance safeguards.
- Multi-repository orchestration.
- Automatic issue tracker synchronization.

## 8. Core Workflows

### 8.1 Repository Onboarding

1. User runs `forge init` in a repository.
2. ForgeCode detects language, package manager, test commands, and docs locations.
3. User reviews generated `.forge/config` and repository summary.
4. ForgeCode stores non-sensitive local metadata.

Acceptance criteria:

- Initialization does not modify source files.
- Generated config is readable and documented.
- User can run `forge status` successfully after init.

### 8.2 Ask Mode

1. User runs `forge ask "How does authentication work?"`.
2. Agent retrieves relevant repository context.
3. Agent answers with file references and confidence notes.
4. No files are modified.

Acceptance criteria:

- Ask mode is read-only.
- Answers cite files or explicitly state when evidence is insufficient.

### 8.3 Plan Mode

1. User runs `forge plan "Add password reset flow"`.
2. Lead developer agent inspects repository context.
3. Product-owner perspective clarifies user value and acceptance criteria.
4. Plan is saved as a task document.
5. ForgeCode requests approval before execution.

Acceptance criteria:

- Plan includes implementation steps, test plan, risks, and approval checklist.
- No implementation files are changed.

### 8.4 Supervised Run Mode

1. User approves a plan.
2. Lead developer decomposes work into subagent-sized tasks.
3. Implementer changes files.
4. Test agent runs validation.
5. QA checks acceptance criteria.
6. Documentation agent updates docs if needed.
7. Final summary is generated.

Acceptance criteria:

- All writes are tied to an approved task.
- Each subagent produces a concise report.
- Final result includes changed files, tests, known issues, and next steps.

### 8.5 Review Mode

1. User runs `forge review`.
2. Agent analyzes current local diff.
3. QA and lead developer perspectives identify bugs, missing tests, and docs gaps.
4. Agent outputs prioritized findings.

Acceptance criteria:

- Review does not modify files unless explicitly requested.
- Findings include severity, location, and suggested fix.

## 9. Human Approval Gates

ForgeCode must support configurable approval modes:

- `readonly`: no writes or shell commands.
- `supervised`: ask before writes, dependency changes, network calls, destructive commands, or test execution.
- `trusted`: allow low-risk writes and configured commands; still require approval for destructive/high-risk actions.

Mandatory approval is required for:

- Deleting, moving, or overwriting many files.
- Running commands outside repository scope.
- Installing dependencies.
- Changing lockfiles.
- Accessing network resources.
- Modifying secrets or environment files.
- Running deploy, publish, release, migration, or infrastructure commands.
- Any action flagged by policy as destructive or irreversible.

## 10. Acceptance Criteria for MVP

The MVP is accepted when:

- A user can initialize a repository with `forge init`.
- A user can ask read-only questions with repository-grounded answers.
- A user can generate a docs-first plan and save it locally.
- A user can approve and run a bounded task through role-based subagent stages.
- The agent can edit files with diff visibility.
- The agent can run configured tests with approval.
- QA can validate acceptance criteria and report unresolved risks.
- Documentation updates can be included when relevant.
- All significant actions are logged.
- The final report clearly states what changed, what was tested, and what remains.
- The MVP works on at least one representative JavaScript/TypeScript repository and one Python repository.

## 11. Release Milestones

### Milestone 0: Product and Architecture Definition

Goal: complete planning artifacts before implementation.

Deliverables:

- Product scope document.
- Architecture overview.
- CLI command specification.
- Agent role specification.
- Safety/approval policy draft.

### Milestone 1: CLI Skeleton and Local Config

Goal: usable command surface with no autonomous editing.

Deliverables:

- CLI entrypoint and command parser.
- `init`, `status`, `config` commands.
- Local config and metadata storage.
- Basic logging.

### Milestone 2: Repository Context and Ask Mode

Goal: read-only repository understanding.

Deliverables:

- File discovery with ignore rules.
- Search and summarization.
- Provider interface.
- `ask` command with file-grounded answers.

### Milestone 3: Docs-First Planning

Goal: convert requests into implementation-ready task plans.

Deliverables:

- `plan` command.
- Task document format.
- Acceptance criteria generator.
- Risk and test-plan sections.
- Approval record.

### Milestone 4: Controlled Implementation Loop

Goal: execute approved tasks with bounded edits.

Deliverables:

- `run` command.
- Lead developer and implementer roles.
- File edit/diff workflow.
- Command approval policy.
- Task state tracking.

### Milestone 5: Test, QA, and Docs Roles

Goal: complete the supervised autonomous loop.

Deliverables:

- Test runner integration.
- QA acceptance validation.
- Documentation update flow.
- Final task report.

### Milestone 6: Hardening and Open-Source Readiness

Goal: prepare for external contributors.

Deliverables:

- Contributor guide.
- Example repositories.
- Security notes.
- Integration tests.
- Release checklist.

## 12. Implementation Backlog

Backlog items are intentionally sized for subagent-driven development. Each item should be small enough for one implementer agent to complete and one QA/test agent to verify.

### Epic A: Product and Technical Documentation

- A1: Write architecture overview. Size: S. Owner: Documentation agent. Acceptance: explains major components and data flow.
- A2: Write CLI command specification. Size: S. Owner: Product owner + documentation agent. Acceptance: includes syntax, options, outputs, and error behavior.
- A3: Write agent role specification. Size: S. Owner: Lead developer agent. Acceptance: defines responsibilities, inputs, outputs, and handoffs.
- A4: Write approval policy specification. Size: M. Owner: QA + lead developer. Acceptance: lists action categories, risk levels, and required approvals.
- A5: Define task file schema. Size: S. Owner: Lead developer. Acceptance: includes plan, approvals, state, subagent reports, and final summary fields.

### Epic B: CLI and Configuration

- B1: Create CLI project skeleton. Size: M. Owner: Implementer. Acceptance: commands can be invoked and return placeholder output.
- B2: Implement `forge init`. Size: M. Owner: Implementer. Acceptance: creates local metadata without touching source files.
- B3: Implement `forge status`. Size: S. Owner: Implementer. Acceptance: displays config, active task, and workspace status.
- B4: Implement `forge config`. Size: M. Owner: Implementer. Acceptance: can read/update supported config fields.
- B5: Add structured logging. Size: M. Owner: Implementer. Acceptance: logs command, timestamp, action type, and outcome.

### Epic C: Repository Context

- C1: Implement file discovery respecting ignore rules. Size: M. Owner: Implementer. Acceptance: excludes ignored files and configured deny patterns.
- C2: Detect language and package manager. Size: S. Owner: Implementer. Acceptance: identifies common JS/TS and Python projects.
- C3: Detect likely test/build commands. Size: M. Owner: Implementer. Acceptance: reports commands from package/config files without executing them.
- C4: Implement content search abstraction. Size: M. Owner: Implementer. Acceptance: returns relevant files and snippets.
- C5: Generate repository summary. Size: M. Owner: Implementer. Acceptance: summary includes structure, technologies, commands, and risks.

### Epic D: Model Provider Interface

- D1: Define provider interface. Size: M. Owner: Lead developer. Acceptance: supports prompt, context, streaming flag, and structured response.
- D2: Implement first provider adapter. Size: M. Owner: Implementer. Acceptance: can answer a simple prompt using configured credentials.
- D3: Add provider configuration validation. Size: S. Owner: Implementer. Acceptance: missing credentials produce actionable errors.
- D4: Add provider capability metadata. Size: S. Owner: Implementer. Acceptance: status output shows configured provider and capabilities.

### Epic E: Ask and Plan Modes

- E1: Implement read-only `forge ask`. Size: M. Owner: Implementer. Acceptance: answers repository questions without file writes.
- E2: Add citation/file-reference formatting. Size: S. Owner: Implementer. Acceptance: responses include relevant paths where evidence exists.
- E3: Implement `forge plan`. Size: M. Owner: Implementer. Acceptance: saves task plan without implementation changes.
- E4: Add acceptance criteria generation. Size: S. Owner: Product owner agent. Acceptance: plans include testable criteria.
- E5: Add plan approval workflow. Size: M. Owner: Implementer. Acceptance: approved/rejected state is stored in task metadata.

### Epic F: Controlled Execution

- F1: Implement task loading for `forge run`. Size: M. Owner: Implementer. Acceptance: loads approved task and rejects unapproved task by default.
- F2: Implement lead developer task decomposition. Size: M. Owner: Lead developer agent. Acceptance: produces subagent-sized steps.
- F3: Implement file edit workflow with diff preview. Size: L. Owner: Implementer. Acceptance: changes are visible before final write in supervised mode.
- F4: Implement shell command approval checks. Size: M. Owner: Implementer. Acceptance: commands are categorized and approval enforced.
- F5: Implement subagent report collection. Size: M. Owner: Implementer. Acceptance: each stage appends a report to task state.

### Epic G: Test, QA, and Documentation Loop

- G1: Implement `forge test` command. Size: M. Owner: Implementer. Acceptance: runs configured tests after approval and records results.
- G2: Implement test-agent result summarization. Size: S. Owner: Test agent. Acceptance: includes command, exit code, pass/fail, and failure snippets.
- G3: Implement QA acceptance validation. Size: M. Owner: QA agent. Acceptance: maps evidence to each acceptance criterion.
- G4: Implement `forge docs` workflow. Size: M. Owner: Documentation agent. Acceptance: proposes documentation updates tied to task changes.
- G5: Implement final task report. Size: S. Owner: Lead developer. Acceptance: reports changed files, tests, QA result, docs, and open issues.

### Epic H: Safety, Audit, and Hardening

- H1: Define command risk classifier. Size: M. Owner: Lead developer + QA. Acceptance: common risky commands are blocked or require approval.
- H2: Add secret-file deny patterns. Size: S. Owner: Implementer. Acceptance: common `.env`, key, and credential files are excluded by default.
- H3: Add audit log viewer. Size: M. Owner: Implementer. Acceptance: user can inspect recent actions.
- H4: Add recovery/rollback notes to task state. Size: S. Owner: Implementer. Acceptance: final report includes rollback guidance where possible.
- H5: Create integration test fixtures. Size: L. Owner: Test agent. Acceptance: JS/TS and Python fixture repos exercise MVP workflow.

## 13. Risk Register

### R1: Unsafe command execution

- Risk: agent runs destructive commands or affects files outside scope.
- Impact: high.
- Mitigation: command risk classification, approval gates, repository boundary checks, audit logs.

### R2: Hallucinated repository understanding

- Risk: agent makes claims or edits not grounded in actual files.
- Impact: high.
- Mitigation: file citations, context retrieval, read-before-write policy, QA validation.

### R3: Scope creep toward full IDE/SaaS

- Risk: MVP becomes too large to ship.
- Impact: medium.
- Mitigation: enforce anti-scope list and milestone gates.

### R4: Model-provider coupling

- Risk: architecture becomes tied to one vendor.
- Impact: medium.
- Mitigation: provider abstraction and capability metadata.

### R5: Poor task decomposition

- Risk: subagents receive tasks too large or vague to complete reliably.
- Impact: medium.
- Mitigation: task sizing rules, lead developer review, acceptance criteria per subtask.

### R6: Secret exposure

- Risk: agent reads, logs, or sends secrets to model providers.
- Impact: high.
- Mitigation: deny patterns, redaction, explicit approval for sensitive files, local audit.

### R7: Test unreliability

- Risk: test commands are missing, flaky, or too expensive.
- Impact: medium.
- Mitigation: command detection, explicit test configuration, result reporting with caveats.

### R8: Open-source trust gap

- Risk: users distrust agent behavior.
- Impact: high.
- Mitigation: transparent logs, simple config, documented safety model, conservative defaults.

## 14. Definition of Done for Backlog Items

Each backlog item is done when:

- Scope is documented or implemented as requested.
- Acceptance criteria are satisfied.
- Relevant tests or documentation are updated.
- Risks and limitations are noted.
- QA review finds no blocking issues.
- Final subagent report lists changed files, validation steps, and follow-up work.

## 15. MVP Default Configuration Principles

- Default mode should be supervised, not fully autonomous.
- Read-only operations should be easy and fast.
- Writes should be explicit, reviewable, and task-linked.
- Destructive operations should be blocked unless specifically approved.
- Repository-local metadata should be human-readable.
- Sensitive files should be excluded by default.
- The agent should prefer small, reversible changes.

## 16. Open Questions

- Which model provider should be first-class in MVP?
- What programming language/runtime should the CLI use?
- Should `.forge/` task metadata be committed by default or treated as local state?
- What exact schema should be used for machine-readable task files?
- Should execution use OS-level sandboxing in v1, or remain policy-based until a later release?
- What license should the project use?

## 17. Recommended Immediate Next Documents

- `docs/product/cli-spec.md`
- `docs/architecture/overview.md`
- `docs/architecture/agent-roles.md`
- `docs/security/approval-policy.md`
- `docs/development/task-schema.md`

These documents should be completed before source-code implementation begins.

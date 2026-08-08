# ForgeCode Agent — Executive Design Review

> Generated after three independent subagents completed architecture, product/scope, and QA/test-suite design. No application code was written before these design artifacts.

**Project folder:** `/Users/ericlara/Documents/OpenSourceCodingAgentLab`  
**Working tool name:** ForgeCode Agent  
**Premise:** Build an original open-source coding agent in the same category as Claude Code/Codex: a CLI/TUI coding teammate that plans, edits, tests, reviews, and commits with human approval gates.

## 1. Design Summary

ForgeCode Agent is designed as a local-first, provider-neutral coding agent with a deterministic controller loop, typed domain boundaries, auditable tool execution, git/worktree isolation, subagent orchestration, and a strict QA-first engineering process.

## 2. Core Architecture Domains

- **Interface layer:** CLI first; optional TUI later. Commands are thin adapters, not business logic.
- **Application layer:** use cases such as `plan`, `run`, `review`, `apply`, `doctor`, and `resume`.
- **Domain layer:** task model, agent loop state machine, tool call intents, review gates, run ledger, policies.
- **Infrastructure layer:** model providers, file/git/shell tools, sandbox adapters, config loader, logs, persistence.
- **QA layer:** fake model provider, fake tools, golden transcripts, security fixtures, deterministic loop tests.

## 3. Clean-Code Patterns Selected

- Hexagonal/ports-and-adapters architecture.
- Command pattern for tool calls.
- State machine for the agent loop.
- Strategy pattern for model providers and context policies.
- Repository pattern for run/session persistence.
- Policy objects for security/approval decisions.
- Immutable/event-sourced run ledger for auditability.

## 4. MVP Scope

- `forgecode init`, `plan`, `run`, `review`, `apply`, `doctor`, `resume`.
- Provider abstraction with at least a fake provider first, then one real provider adapter.
- Read/search/patch/file tools, shell execution behind allow/deny policy, git diff/status/worktree support.
- Human approval gates for writes, shell commands, commits, network access, and external delivery.
- Subagent-style role loop documented in `agents/`, with reviewer roles never approving their own work.

## 5. QA Strategy

- TDD is mandatory: no production behavior without a failing test first.
- Golden transcript tests validate deterministic agent loops.
- Fake model provider and fake tools are first-class test infrastructure.
- Security tests include prompt injection, shell injection, path traversal, secrets exposure, and unsafe git operations.
- CI gates: unit, integration, security abuse tests, golden replay, lint/typecheck.

## 6. Diagrams

### Domain / Context Diagram

```mermaid
flowchart LR
    User[Developer / Maintainer]
    Repo[(Local Git Repository)]
    Config[(User + Repo Config)]
    Memory[(Project and Session Memory)]
    Providers[Model Providers\nHosted or Local]
    Plugins[Plugins\nTools / Context / Subagents]
    Shell[Local Shell / Sandbox]
    Git[Git / Worktrees]
    CI[Optional CI / Remote Checks]

    subgraph ForgeCode[ForgeCode Agent]
        CLI[CLI]
        TUI[Optional TUI]
        App[Session Controller\nApprovals + Use Cases]
        Runtime[Agent Runtime\nLoop + Coordinator]
        Context[Context Service\nRepo Map + Retrieval]
        Policy[Policy Engine\nPermissions + Risk]
        Patch[Patch Manager\nDiffs + Apply + Revert]
        Sandbox[Sandbox Executor\nCommands + Logs]
        Obs[Observability\nEvents + JSONL Traces]
        Registry[Plugin Registry]
    end

    User --> CLI
    User --> TUI
    CLI --> App
    TUI --> App
    App --> Runtime
    App --> Policy
    Runtime --> Context
    Runtime --> Patch
    Runtime --> Sandbox
    Runtime --> Registry
    Runtime --> Obs
    Context --> Repo
    Context --> Memory
    Context --> Config
    Runtime --> Providers
    Registry --> Plugins
    Policy --> Sandbox
    Policy --> Patch
    Patch --> Repo
    Patch --> Git
    Sandbox --> Shell
    Sandbox --> Repo
    Sandbox --> CI
    Obs --> Memory
    Git --> Repo

```

### Agent Loop Flow Diagram

```mermaid
flowchart TD
    A([User task received]) --> B[Intake\nrequest + repo + git status]
    B --> C{Task requires code changes?}
    C -- No --> D[Build read-only context]
    D --> E[Answer / explain / review]
    E --> Z([Complete])

    C -- Yes --> F[Build context\nfiles + symbols + tests + memory]
    F --> G[Plan\ntargets + tools + risks + verification]
    G --> H{Approval required?}
    H -- Yes --> I[Show plan/action scope]
    I --> J{User approves?}
    J -- No --> K[Revise plan or stop]
    K --> Z
    H -- No --> L[Execute next action]
    J -- Yes --> L

    L --> M{Action type}
    M -- Read/Search --> N[Context tool]
    M -- Patch --> O[Patch proposal]
    M -- Shell/Test --> P[Sandbox command]
    M -- Delegate --> Q[Subagent task packet]

    N --> R[Update trace + context]
    O --> S{Patch safe to apply?}
    S -- No --> T[Re-read/rebase or request approval]
    T --> R
    S -- Yes --> U[Apply patch + git checkpoint]
    U --> R
    P --> V[Capture output + diagnostics]
    V --> R
    Q --> W[Collect structured findings / patch proposal]
    W --> R

    R --> X{Plan complete?}
    X -- No --> L
    X -- Yes --> Y[Verify\ntests + lint + diff review]
    Y --> AA{Verification passed?}
    AA -- Yes --> AB[Summarize changes\nverification + risks]
    AB --> Z
    AA -- No --> AC{Budget remains?}
    AC -- Yes --> AD[Repair loop\nclassify failure + update plan]
    AD --> L
    AC -- No --> AE[Stop with failure report\nlogs + next actions]
    AE --> Z

```

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant UI as CLI/TUI
    participant App as Session Controller
    participant PE as Policy Engine
    participant AR as Agent Runtime
    participant CS as Context Service
    participant MP as Model Provider
    participant SA as Subagent Coordinator
    participant PM as Patch Manager
    participant SB as Sandbox Executor
    participant GT as Git/Worktree Manager
    participant LOG as Event Log

    U->>UI: Request coding task
    UI->>App: Start/resume session
    App->>GT: Read branch, HEAD, dirty status
    GT-->>App: Repository state
    App->>PE: Evaluate mode and permissions
    PE-->>App: Approval requirements
    App->>AR: Run task with policy and repo state
    AR->>CS: Build relevant context
    CS-->>AR: Files, symbols, tests, memories
    AR->>MP: Ask for plan with grounded context
    MP-->>AR: Structured plan
    AR->>LOG: Record plan event

    alt Plan or action needs approval
        AR-->>App: Approval request with scope/risk
        App-->>UI: Display approval prompt
        U->>UI: Approve / deny / revise
        UI->>App: Decision
        App->>PE: Record decision
    end

    opt Parallel bounded delegation
        AR->>SA: Dispatch Scout/Verifier/Reviewer packets
        SA->>CS: Read/search allowed context
        SA->>MP: Specialized reasoning calls
        SA-->>AR: Findings and patch proposals
        AR->>LOG: Record subagent results
    end

    AR->>PM: Create minimal patch proposal
    PM->>GT: Check file freshness and checkpoint
    GT-->>PM: Safe to apply or conflict
    PM-->>AR: Diff preview

    alt Patch permitted
        AR->>PM: Apply patch
        PM->>GT: Update working tree/checkpoint metadata
        PM-->>AR: Applied diff
    else Conflict or denied
        PM-->>AR: Rebase required or stop reason
    end

    AR->>SB: Run verification command under sandbox policy
    SB->>PE: Check command/network/write permission
    PE-->>SB: Allow / require approval / deny
    SB-->>AR: Exit code, output, diagnostics
    AR->>LOG: Record command result

    alt Verification failed and budget remains
        AR->>MP: Diagnose failure and repair plan
        MP-->>AR: Repair action
        AR->>PM: Apply repair patch
        AR->>SB: Re-run targeted verification
    end

    AR-->>App: Final result summary, diff, verification status
    App-->>UI: Render final response
    UI-->>U: Changes, tests, risks, next steps

```

## 7. Human Review Gates

- Approve product direction before broad feature expansion.
- Approve any real provider integration secrets/config.
- Approve any operation that pushes, publishes, installs global packages, or contacts external services.
- Approve license choice before public release. Recommended default: Apache-2.0 or MIT, with Apache-2.0 preferred if patent language matters.

## 8. Immediate Implementation Plan

1. Establish project metadata and package skeleton.
2. Write fake-provider and domain-state tests first.
3. Implement minimal domain models to satisfy tests.
4. Add tool interfaces and fake tool registry.
5. Implement deterministic controller loop with approval states.
6. Add CLI wrapper only after the domain loop is tested.
7. Run independent spec and quality review after each slice.

## 9. Source Design Documents

- Architecture research: `docs/architecture/architecture-research.md`
- Product scope: `docs/product/feature-scope.md`
- QA strategy: `docs/qa/qa-test-strategy.md`
- Initial test suite design: `docs/qa/initial-test-suite-design.md`
- Diagrams: `docs/diagrams/*.mmd`

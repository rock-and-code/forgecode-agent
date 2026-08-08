# ForgeCode Agent Team Autonomous Loop

## Purpose
Run development without constant supervision while preserving human review gates.

## Sprint Tick
1. Product Owner selects exactly one unfinished backlog slice.
2. Lead Developer converts it into a 2–5 minute TDD task.
3. Test Engineer writes/updates the failing test first.
4. Implementer writes the minimum production code to pass.
5. QA Reviewer performs spec-compliance review.
6. Security/Sandbox Reviewer reviews unsafe tool, prompt, path, shell, secret, and git behavior.
7. Docs Developer updates docs/manual if user-visible behavior changed.
8. Release Engineer runs gates and records results.
9. Human approval is required before push, publish, external network side effects, or destructive commands.

## Gate Types
- Pre-flight gate: check scope, dirty working tree, dependencies, and approval requirements.
- Revision gate: reviewer rejects with exact fixes; implementer fixes only those issues.
- Escalation gate: unclear requirement or unsafe side effect requires Eric's review.
- Abort gate: stop if tests cannot be made deterministic or safety boundary is unclear.

## Status Rooms
- `rooms/implementation/`: slice handoffs and work notes.
- `rooms/reviews/`: spec, QA, and security reviews.
- `rooms/decisions/`: human decision records and architecture decisions.
- `rooms/research/`: research notes and source links.

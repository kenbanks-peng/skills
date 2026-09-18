# Worker workflow

Execute the delegated card or bounded scope. The orchestrator owns board updates and dependency reconciliation; return findings to it rather than editing cards or moving columns.

1. Read the assignment's scope, acceptance criteria, dependencies, file boundaries, and required verification. Resolve missing instructions or ownership conflicts with the orchestrator before proceeding.
2. Implement within the assigned boundaries and verify each acceptance criterion. Report blockers or prerequisite changes promptly, with evidence and the action needed to proceed.
3. Return board/card references, delivered changes, verification results (including failed or unrun checks), blockers, and remaining work with a Handoff action: the concrete starting point for the next agent or session. On interruption, return the same information as a handoff.

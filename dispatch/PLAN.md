# New Dispatch Skill — Product Requirements

## Goal

Build a greenfield dispatch skill that uses tuios as its primary multiagent work system. Use native tuios capabilities for isolation, assignment, coordination, review, delivery, recovery, and visibility. Do not preserve the current design or require backward compatibility.

## 1. Product outcome

- Take a coding objective from task planning through implementation, review, verification, integration, and cleanup.
- Run independent work in parallel. Respect dependencies and serialize integration where required.
- Continue authorized work without human questions or approval requests. Record blockers and continue independent work when possible.
- Give clear evidence of delivered changes, check results, remaining work, and retained resources.

## 2. Tuios-first design

- Prefer documented tuios tools over custom orchestration code that provides the same function.
- Use tuios recipes as the basis for supported workflows. Recipes are documented procedures, not another scheduling service.
- Use the installed tuios capability documentation as the source of command syntax and behavior.
- Use native agent, worktree, review, checkpoint, ship, queue, mail, wait, and dashboard features as one workflow.
- Do not require every worker to share the orchestrator's session.
- Do not use every feature merely to increase tool usage. Each selected feature must serve a product requirement.

## 3. Tasks and execution modes

- Keep durable objectives, task requirements, acceptance criteria, dependencies, assignments, and outcomes in Aven.
- Use tuios for live execution and coordination, not a second custom scheduler.
- Support distinct tasks assigned to separate workers.
- Support competing implementations of one task through tuios fan-out.
- Support implementation, review, and verification agents with clear roles.
- Set concurrency from the objective and available resources. Prevent conflicting assignments in the same checkout.

## 4. Native worktrees and fleet

- Use tuios worktrees and their sessions as the standard worker isolation model.
- Use native worktree creation, inventory, diff, and removal instead of parallel manual worktree management.
- Keep orchestration and shared status surfaces separate from worker sessions.
- Track the relationship between each task, attempt, agent pane, session, branch, worktree, and execution environment.
- Use fleet selectors for owned-worker inventory, grouped status, messages, and waits.
- Use fan comparison, verification, diffs, and verdicts for competing attempts where supported by the agent's role and grants.
- Keep and integrate the selected result. Clean up other attempts according to their recorded disposition.

## 5. Agent launch and integration

- Prefer native agent launch and readiness support over custom terminal launch logic.
- Require accurate working, idle, done, needs-input, and error state reporting for supported workers.
- Support pi workers with a tested tuios integration. Do not infer tool completion solely from terminal silence.
- If containers are used, preserve native tuios identity, state, communication, checkpoint, and review behavior across the container boundary.
- Retain direct runtime operations only for functions tuios does not provide, such as container lifecycle management.

## 6. Assignment, queue, and mail

- Use native initial prompts for assignments and ask-agent for immediate agent questions.
- Use queue for authorized follow-up work when an agent is busy, including review corrections.
- Use mail for asynchronous coordination, with explicit reads, replies, and thread-specific waits where needed.
- Keep acceptance criteria and durable outcomes in task records. Queue and mail supplement those records.
- Prevent duplicate assignments after interruption or uncertain delivery.
- Treat agent replies as evidence, not authority to change scope or permissions.

## 7. Event-driven progress

- Use native waits and events for readiness, state changes, messages, command completion, and process exit.
- Use grouped waits to monitor the fleet rather than repeatedly inspecting workers one by one.
- Use pane capture and prompt inspection for diagnosis, not as the primary scheduler.
- Detect stalled work and failures, then retry or repair within the authorized scope.
- Never answer a worker's approval prompt on behalf of the user.

## 8. Review and checkpoints

- Use native review diffs and line or hunk notes for feedback.
- Send review feedback through native delivery and queue mechanisms.
- Use checkpoints to inspect turn-level changes and recover from unsuccessful work.
- Preserve useful checkpoints until the attempt's disposition is known.
- Coordinate checkpoint restoration with worker state so no concurrent writer competes with restoration.
- Verify task acceptance criteria and dispatcher-selected checks before delivery.

## 9. Commit and delivery

- Use ship commit as the standard commit operation for completed worker changes.
- Keep task checkouts dedicated to their assignments so ship commit captures the intended deliverable.
- Use ship merge as the standard integration operation, with an explicit target and merge policy.
- Use native ship status for existing pull-request and CI visibility.
- Retain reviewed commit identities, delivery evidence, and check results in durable records.
- Do not use ship push or ship pr in unattended execution while they require human approval. Do not bypass their approval controls.

## 10. Dashboard and observability

- Provide a live, read-only TML dashboard for the dispatch run.
- Show task dependencies, worker states, active attempts, queued work, review results, checks, delivery status, blockers, and cleanup status.
- Update the existing surface as work changes instead of emitting repeated static summaries.
- Use native pane, session, worktree, and agent labels so users can locate work directly.
- Keep the dashboard in the dispatcher's visible workspace. Show active Linux workers through native pane views or hosted panes, with host-qualified addresses.
- Remove unused starter shells. Reuse check panes and close completed temporary panes after saving results. Do not accumulate failed check windows.
- Arrange only owned run workspaces. Do not move the user's focus or switch their client to provide status.
- Keep the dashboard free of questions, approval actions, and input forms.

## 11. Recovery and cleanup

- Resume by reconciling durable task records with native tuios inventories and observed repository and runtime state.
- Reuse existing resources and queued assignments when their identities are known. Do not repeat launches, commits, or merges solely because output was lost.
- Keep only the run metadata needed to link tasks, resources, decisions, and evidence. Do not reproduce tuios's internal state in a custom control system.
- Use native worktree and fleet cleanup for owned resources after their outcomes are recorded.
- Preserve unrelated resources and useful unresolved work.
- Distinguish delivered work from completed cleanup in the final status.

## 12. No human-input workflow

- Do not use ask-human, manual questions, approval forms, or commands that initiate human approval requests.
- Make decisions from the supplied objective, repository context, documented defaults, and existing authorization.
- When authorization or required information is absent, record a precise blocker. Continue independent work or end with a blocked result.
- Respect forbidden responses. Do not seek the same result through another command.

## Acceptance criteria

- A distinct-task run uses native worktree sessions, agent coordination, grouped monitoring, review, ship commit, ship merge, and cleanup.
- A competing-attempt run uses native fan-out, comparison, verification, selection, and disposition of the other attempts.
- A busy worker receives a queued correction and completes it without a duplicate assignment.
- A checkpoint can be inspected and restored in a controlled recovery exercise.
- An interrupted run resumes without duplicate workers or repeated delivery.
- A live dashboard reflects task, worker, review, check, delivery, and cleanup changes. Its overview is readable at 80 columns.
- A Linux run shows actual Linux workers and native state, runs checks on Linux, and pulls the selected result for local review/delivery.
- Final pane inventory contains no abandoned starter shells, check commands, reviewer panes, or worker views.
- No supported path asks the user a question or initiates an approval request.
- The resulting skill documents capability gaps explicitly and does not retain old architectural restrictions as requirements.

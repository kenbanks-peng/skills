---
name: plan-execution
description: Use when executing existing multi-phase implementation plans from disk through scheduled Hermes cron runs, with a dedicated git worktree, local verification, checkpoint commits, and durable phase status in the plan file.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, implementation, execution, branches, worktrees, cron]
    related_skills: [writing-plans, subagent-driven-development, github-repo-management]
---

# Plan Execution

## Overview

Sequentially execute an existing multi-phase plan from disk through CRON. The plan file is canonical.

Use this workflow when CRON should resume and advance plan phases across runs, with durable status recorded in the plan file.

The default execution model is a single plan branch in a dedicated git worktree. CRON ticks select one eligible phase, make scoped changes, run local verification, update durable phase status, and commit checkpoints.

## When to Use

Use this skill when:

- The user has an existing implementation plan on disk.
- The plan has multiple phases that should be executed sequentially.
- CRON should resume and advance plan phases across runs.
- Progress must survive across sessions and agent runs.
- Git commits should checkpoint each completed phase.
- The plan file should remain the canonical status source.

Do not use this skill when:

- The user only wants a one-off plan review.
- The task has no durable plan file.
- The user wants immediate interactive execution only, with no scheduled continuation.
- Destructive git cleanup, branch deletion, merging, or worktree removal is required without explicit authorization.

## Tools

- File tools: read and patch plan files.
- Terminal: git and local verification.
- `todo`: session tracking only.
- `delegate_task`: optional isolated implementation or review.
- `cronjob`: required.
- macOS CRON keep-awake setup: terminal is required during bootstrap on macOS.

## Plan File Contract

The plan file must contain:

- A durable `## Phase Status` table.
- A stable phase number and title for each executable phase.
- Enough phase detail elsewhere in the plan to identify scoped work.
- Optional `## CRON Bootstrap` state once scheduled execution is enabled.

Phase selection is based on the `## Phase Status` table. Phase implementation scope is based on the matching numbered/title phase content in the plan.

## Phase Status

Every plan ends with:

```markdown
## Phase Status

| Number | Title | Status |
| -----: | ----- | ------ |
|      1 | Example phase | TODO |
```

Valid statuses: `TODO`, `IN PROGRESS`, `DONE`, `DEFERRED`, `FAILED`, `BLOCKED`, `SKIPPED`.

Allowed transitions:

- `TODO -> IN PROGRESS -> DONE`
- `TODO/IN PROGRESS -> DEFERRED`
- `IN PROGRESS -> FAILED`
- `TODO/IN PROGRESS -> BLOCKED`
- `TODO -> SKIPPED`

Keep the table simple: `Number | Title | Status`. Do not add timestamp columns by default.

Update the table as each phase is claimed and completed. Before writing, confirm the table has not changed unexpectedly since it was read:

1. Save the exact `## Phase Status` table text read at the start of the tick.
2. Re-read the plan immediately before patching.
3. Compare the current table text to the saved table text.
4. Allow only the intended status transition for the selected phase.
5. Stop if any unrelated row, title, number, or status changed.

## Repo Root and Worktree Resolution

Never assume the current working directory is the repo root. The repo root may be one or more directories above the directory being worked in.

During bootstrap and every CRON tick:

1. Run `git rev-parse --show-toplevel`.
2. Treat that absolute path as `repo_root`.
3. Resolve the plan path to an absolute path.
4. If the plan path is inside the repo, record its path relative to `repo_root`.
5. Run git commands from `repo_root` during bootstrap or from the dedicated execution worktree root during CRON ticks.
6. Run verification commands from the execution worktree root unless a command explicitly declares another working directory.

Default execution worktree path:

```text
<repo-root-parent>/<repo-root-name>.plan-<slug>
```

The worktree path is based on the resolved git repo root, not on the agent's initial current working directory.

## Git Rules

Preflight:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

Rules:

- Validate generated branch names with `git check-ref-format --branch`.
- Default plan branch: `plan/<slug>`.
- Default strategy: single execution branch. Run all phases sequentially on `plan/<slug>` in the dedicated execution worktree.
- Do not create per-phase branches by default.
- Do not merge, rebase, delete, reset, clean, remove worktrees, or run destructive git commands unless explicitly authorized.
- Do not remove worktrees with uncommitted changes.

## Branch and Worktree Strategy

Default strategy: single execution branch in a dedicated worktree.

- Use `plan/<slug>` as the durable execution branch.
- Commit each completed phase directly on this branch.
- Use a dedicated worktree for `plan/<slug>` so scheduled work does not interfere with the user's active checkout.
- Create or reuse the dedicated worktree during bootstrap before creating the CRON job.
- If the predictable worktree path already exists, reuse it only if it is already a git worktree for the intended `plan/<slug>` branch and is clean. Otherwise stop.
- Do not create suffixed alternate worktrees automatically. Avoid splitting execution across multiple worktrees.

Base branch derivation during bootstrap:

- If the current checkout is on a non-detached branch, use that branch as the base.
- If the current checkout is detached, use the remote default branch if detectable.
- If no base branch can be derived safely, stop.
- Record the derived base branch in `## CRON Bootstrap`.

Bootstrap requires a clean original checkout. If `git status --short` in the original checkout is non-empty during bootstrap, stop before creating the CRON job. Do not create or enable scheduled execution from an uncommitted state, because the execution worktree will not include those changes.

## CRON Bootstrap

CRON bootstrap is an initiating handoff, not an execution tick.

If `## CRON Bootstrap` is absent or incomplete:

1. Resolve `repo_root` with `git rev-parse --show-toplevel`.
2. Resolve and record absolute and repo-relative plan paths.
3. Run git preflight in the original checkout.
4. Stop before creating CRON if the original checkout has uncommitted changes.
5. Derive and record the base branch.
6. Create or reuse the dedicated execution worktree for `plan/<slug>`.
7. On macOS, ensure a per-user keep-awake LaunchAgent is installed and loaded before creating the CRON job.
8. Create the CRON job, attaching this skill by name.
9. Compare the returned CRON job fields to the intended bootstrap values, especially `job_id`, `name`, `schedule`, `deliver`, `workdir`, attached `skills`, and enabled/scheduled state.
10. Record concrete bootstrap state in the plan. If delivery resolves differently than expected (for example, a CLI-origin run returns `deliver: local`), record the actual returned value and keep the prompt/bootstrap section consistent with it.
11. Update any CRON bootstrap status row.
12. Commit if appropriate.
13. Report the job id/name/schedule, actual delivery mode, and macOS keep-awake status.
14. End the current run.

Required parameters:

- schedule
- repo root, absolute plan path, and repo-relative plan path
- plan slug
- base branch
- plan branch: `plan/<slug>`
- execution worktree path
- max phases per run; default is `1`
- verification commands, or instructions to derive obvious local checks if none are configured
- delivery target, if not using the current conversation default
- self-stop identity
- self-stop action: default `pause`; use `remove` only if requested

Required section:

```markdown
## CRON Bootstrap

Status: enabled
Job name: run-<plan-slug>
Job id: <id-or-unknown>
Schedule: <schedule>
Repo root: <absolute-repo-root>
Plan path: <absolute-plan-path>
Plan relative path: <repo-relative-plan-path>
Plan slug: <plan-slug>
Base branch: <base-branch>
Plan branch: plan/<plan-slug>
Execution worktree: <absolute-worktree-path>
Max phases per run: 1
Verification commands: <commands-or-derive-obvious-local-checks>
Self-stop action: pause
Delivery target: <target-or-origin>
macOS keep-awake: <not-applicable-or-enabled:com.hermes.keepawake>
```

After creating or starting the CRON job, recording `## CRON Bootstrap`, updating any bootstrap status row, and reporting the job id/name/schedule, the initiating agent is done. Do not execute an implementation phase in the same run unless the user explicitly requested bootstrap plus immediate execution.

## macOS Keep-Awake Integration

On macOS, scheduled Hermes CRON work pauses while the machine is asleep. During CRON bootstrap, install and load a per-user LaunchAgent that runs `caffeinate` so the Mac stays awake while plugged in. This is part of the skill's default integrated bootstrap; do not merely suggest it to the user.

Use a user LaunchAgent rather than `sudo pmset` by default:

- It does not require a password prompt.
- It is reversible without changing global power settings.
- It allows the display to sleep while preventing idle/system sleep for scheduled work.
- It survives logout/login as long as the user session and LaunchAgent domain are available.

Bootstrap command:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$HOME/Library/LaunchAgents/com.hermes.keepawake.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.hermes.keepawake</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/caffeinate</string>
      <string>-ims</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/com.hermes.keepawake.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/com.hermes.keepawake.err</string>
  </dict>
</plist>
EOF
plutil -lint "$HOME/Library/LaunchAgents/com.hermes.keepawake.plist"
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.hermes.keepawake.plist" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.hermes.keepawake.plist"
launchctl enable "gui/$(id -u)/com.hermes.keepawake"
launchctl kickstart -k "gui/$(id -u)/com.hermes.keepawake"
```

Verification command:

```bash
launchctl print "gui/$(id -u)/com.hermes.keepawake" >/dev/null && \
pmset -g assertions | grep -E 'caffeinate|PreventUserIdleSystemSleep|PreventSystemSleep' || true
```

Record the result in `## CRON Bootstrap` as one of:

- `macOS keep-awake: enabled:com.hermes.keepawake`
- `macOS keep-awake: not-applicable`
- `macOS keep-awake: failed:<brief-reason>`

If keep-awake setup fails during interactive bootstrap, stop and report the failure before creating the CRON job. If it fails during unattended CRON, report the failure and do not modify phase status.

Do not click System Settings permission prompts or type passwords. If macOS requires user permission or admin credentials, stop and report exactly what is needed.

## CRON Prompt

The CRON job must attach/load this skill by name: `git-managed-plan-execution`.

The prompt should mention the skill by name and include enough concrete bootstrap values for unattended execution:

- repo root, plan path, and execution worktree path
- plan branch and base branch
- CRON bootstrap state
- verification commands or derive-obvious-checks instruction
- commit format
- self-stop identity and action

Do not paste the entire skill contents into the CRON prompt. The cron job should load the skill and use the concrete values recorded in the plan.

CRON runs are unattended and must not ask the user questions. If required input is missing, derive it when safe; otherwise choose a predefined outcome: stop silently, mark `BLOCKED`, mark `FAILED`, or report, depending on the rules below.

Each CRON run must re-read the plan, run git preflight in the execution worktree, execute at most one eligible `TODO` phase, run local verification, update phase status, commit verified changes, and report the result when appropriate.

When all phases are complete and verified, pause the CRON job by default; remove it only if configured.

## Verification Rules

Verification commands are the repo-specific commands used to prove the phase is complete, such as tests, lint, type checks, or builds.

- Run configured verification commands from the execution worktree root unless a command explicitly declares another working directory.
- If no verification commands were captured during bootstrap, derive obvious local checks from repo files such as `Makefile`, `package.json`, `pyproject.toml`, `Cargo.toml`, or similar project manifests.
- Run the strongest obvious local checks and record what was run.
- Treat non-zero exits as verification failures.
- Do not mark a phase `DONE` while lint, build, type checks, or tests are failing.
- If verification fails, attempt scoped fixes and re-run verification.
- Target zero errors and zero warnings where feasible.
- Use up to three verify/fix cycles per tick.
- If verification still fails after bounded repair attempts, mark the phase `FAILED` or `BLOCKED` depending on cause, and commit the terminal plan-status update when safe.

## Execution Workflow

Each CRON tick executes at most one phase.

1. Read the plan from disk.
2. Parse the `## Phase Status` table.
3. Run git preflight in the execution worktree.
4. Apply stop conditions to the git preflight result.
5. Ensure CRON bootstrap is complete.
6. Apply stop conditions to the phase status table.
7. Select the first `TODO` phase.
8. Mark the selected phase `IN PROGRESS` in the plan file.
9. Do not commit the `IN PROGRESS` claim by default.
10. Execute only that phase's scoped work.
11. Run local verification.
12. If verification fails, attempt scoped fixes and re-run verification, up to three verify/fix cycles.
13. Inspect diffs.
14. If the phase is large/high-risk, run an independent review after verification passes.
15. Fix substantive review findings and re-run verification before marking `DONE`.
16. If verification and required review pass, update phase status to `DONE`.
17. Commit scoped verified implementation changes plus the final `DONE` plan-status update together.
18. If work cannot be completed, update phase status to `FAILED`, `BLOCKED`, `DEFERRED`, or `SKIPPED` and commit that terminal plan-status update when safe.
19. Re-check `git status --short`.
20. Run completion verifier.

If a selected phase is already satisfied and requires no implementation changes, run verification, update the phase to `DONE`, and commit the plan-status-only change.

## Review Rules

Independent review is optional for normal phases and required for large/high-risk phases.

A phase is large/high-risk if either condition applies:

- Diff size threshold: more than 5 files changed or more than 300 lines of diff.
- Risk category: auth, payments, security, data deletion, migrations, production configuration, CI/CD, secrets, permissions, public API changes, or similar high-impact work.

For large/high-risk phases:

1. Run local verification first.
2. Review the stable verified diff, optionally with `delegate_task`.
3. Fix substantive review findings.
4. Re-run verification.
5. Mark `DONE` only after verification and required review findings are resolved.

The parent CRON agent remains responsible for final verification, status updates, and commits. Do not let a subagent perform final commits or durable status updates without parent verification.

## Commit Protocol

Commit at least once per completed phase.

Format:

```text
plan:<plan-slug> phase:<N> <keyword>
```

Recommended keywords:

- `done`
- `failed`
- `blocked`
- `deferred`
- `skipped`

Rules:

- Keep messages terse.
- Include plan slug and phase number.
- Do not commit the `IN PROGRESS` claim by default.
- When verification and required review pass, commit implementation changes and the final `DONE` status update together.
- Always commit terminal plan-status updates for `DONE`, `FAILED`, `BLOCKED`, `DEFERRED`, or `SKIPPED` when safe.
- If implementation changes are unverified or unsafe, do not commit them.
- It is acceptable to commit only the plan-file status update when recording `FAILED`, `BLOCKED`, `DEFERRED`, or `SKIPPED`.
- Inspect status/diffs before commit and status after commit.

## CRON Shutdown

At the end of every CRON tick, check the `## Phase Status` table.

If every phase is `DONE`:

1. Run configured or derived verification commands.
2. Check `git status --short`.
3. If verification passes and the worktree is clean, apply the configured self-stop action.
4. Report the shutdown result through the cron result.

Do not write shutdown state back into the plan by default. Avoid making the worktree dirty immediately before the final clean-status check.

Default self-stop action is `pause`. Use `remove` only when configured.

## Cleanup

Do not clean worktrees, delete branches, merge branches, or run destructive git commands unless the user explicitly asks.

Before any user-authorized cleanup, report the current branches, worktrees, commits, changed files, and verification status.

## Stop Conditions

During interactive bootstrap, stop and report when:

- required input is missing or ambiguous and cannot be derived safely
- the original checkout has uncommitted changes
- the base branch cannot be derived safely
- the expected execution worktree path exists but is not the intended clean worktree for `plan/<slug>`
- user authorization is required
- a destructive git action would be needed
- a branch, worktree, merge, or plan-status conflict occurs

During unattended CRON ticks, stop silently when:

- any phase is already `IN PROGRESS`
- any phase is already `IN PROGRESS` and the execution worktree is dirty

During unattended CRON ticks, stop and report when:

- the execution worktree has uncommitted changes and no phase is `IN PROGRESS`
- the phase status table changed unexpectedly since it was read
- unrelated uncommitted changes are present
- verification fails after up to three scoped verify/fix cycles
- user authorization would be required
- a destructive git action would be needed
- a branch, worktree, merge, or plan-status conflict occurs

During unattended CRON ticks, do not ask the user questions. Mark `BLOCKED` or `FAILED` and commit the terminal plan-status update when safe.

## Common Pitfalls

1. Treating the session todo list as durable state.
   The plan file is canonical. `todo` is only for the current run.

2. Running more than one phase per CRON tick.
   Default to one eligible `TODO` phase per run unless the bootstrap state explicitly says otherwise.

3. Forgetting to end after CRON bootstrap.
   The initiating run should create/start the CRON job, record bootstrap state, commit if appropriate, report the job, and stop.

4. Assuming the current working directory is the repo root.
   Always resolve `repo_root` with `git rev-parse --show-toplevel` and derive the execution worktree from that root.

5. Updating phase status without re-reading the table.
   Before patching the plan, confirm the `## Phase Status` table has not changed unexpectedly.

6. Committing unrelated changes.
   Inspect `git status --short` and diffs before every commit. Stop if unrelated changes are present.

7. Committing `IN PROGRESS` by default.
   The default is to leave the claim uncommitted during the active tick and commit only terminal status updates.

8. Marking `DONE` before verification and required review pass.
   `DONE` requires passing verification and resolved required review findings.

9. Pausing or removing the wrong CRON job.
   Use the recorded job id/name from `## CRON Bootstrap`; list jobs when identity is uncertain.

10. Recording intended CRON settings instead of returned CRON settings.
   After `cronjob(action='create')`, record the actual returned `job_id`, `deliver`, `workdir`, `skills`, and schedule state. Delivery can legitimately resolve to `local` in CLI-origin contexts even when the unattended prompt text says `origin`; keep the prompt and bootstrap block consistent with the returned job.

11. Skipping macOS keep-awake during bootstrap.
   On macOS, install and verify `com.hermes.keepawake` before creating the CRON job. Otherwise CRON can pause whenever the machine sleeps.

12. Performing cleanup too early.
   Do not delete branches, remove worktrees, merge, reset, or clean unless explicitly authorized.

## Verification Checklist

- [ ] Plan file was re-read from disk.
- [ ] `## Phase Status` table parsed successfully.
- [ ] Repo root was resolved with `git rev-parse --show-toplevel`.
- [ ] Dedicated execution worktree for `plan/<slug>` was used.
- [ ] Git preflight completed.
- [ ] No unrelated uncommitted changes were present.
- [ ] CRON bootstrap state is complete.
- [ ] On macOS, `com.hermes.keepawake` was installed/verified or a keep-awake failure was reported before CRON creation.
- [ ] At most one eligible `TODO` phase was selected.
- [ ] Selected phase was marked `IN PROGRESS` before work began.
- [ ] The `IN PROGRESS` claim was not committed by default.
- [ ] Local verification commands were run or obvious repo checks were derived and run.
- [ ] Up to three verify/fix cycles were attempted if verification failed.
- [ ] Large/high-risk phases received required review after verification passed.
- [ ] Substantive review findings were fixed and verification re-run.
- [ ] Diffs were inspected before commit.
- [ ] Scoped verified changes and final `DONE` status were committed together, or a terminal status-only commit was made when appropriate.
- [ ] Phase status was updated to `DONE`, `FAILED`, `BLOCKED`, `DEFERRED`, or `SKIPPED`.
- [ ] Final `git status --short` was checked.
- [ ] Completion/shutdown conditions were evaluated.
- [ ] CRON job pause/remove action was applied only when configured and safe.

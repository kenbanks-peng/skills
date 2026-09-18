# Establish or recover the project board

Read this when `.taskboard/settings.md` is missing, incomplete, contradictory, or references an unavailable board. Paths beginning with `.taskboard/` are relative to the project root.

## Missing settings

1. If another checkout or agent already has the project's board reference, use that reference rather than creating another board. When several agents start together, agree one initializer and share its reference.
2. Create `.taskboard/` if needed. If no shared reference exists, create a board named for the project. Never list boards or search for a project-name match: the saved reference identifies the board, not its name.
3. Immediately write `.taskboard/settings.md` with the actual board ID supplied or returned by Doska:

   ```yaml
   ---
   board_id: "<actual board ID>"
   ---
   ```

   No Markdown body is required. Keep the file shareable through version control, but do not commit it without authorization.

4. Confirm the write succeeded before continuing. Other checkouts need this same reference before using the workflow; missing copies are not a reason to create another board.
5. For a newly created board, establish **Backlog → Ready → In Progress → Review → Done**, with **Blocked** for work waiting on an external dependency. Reuse suitable default columns and designate Done as the completion column. For a shared existing board, follow its conventions rather than restructuring it.

Return to the main workflow once the reference is saved and the board is accessible with its workflow established.

## Incomplete or contradictory settings

Resolve the reference before creating anything. Preserve existing fields and notes. Ask the user when the correct reference cannot be established from available evidence.

## Referenced board unavailable

Preserve the reference and report the problem. Replacing the board requires the user's approval.

## Creation result uncertain

Recover the returned reference if possible; otherwise ask for the board reference or confirmation that creation failed before retrying. An uncertain response is not permission to create another board.

## Board created but settings save failed

Report the board ID and the save failure so the reference can be restored without recreating the board. Resume setup by saving that reference, not by creating another board.

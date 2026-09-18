# Establish or recover the project board

Use when `.taskboard/settings.md` at the project root is missing or unusable.

## Missing settings

1. Designate one initializer to create a project-named board.
2. Save the returned ID in `.taskboard/settings.md`:

   ```yaml
   ---
   board_id: "<board ID>"
   ---
   ```

3. Share this file across checkouts.
4. Establish **Backlog → Ready → In Progress → Review → Done**, plus **Blocked**. Reuse suitable default columns and designate Done as the completion column.

## Recovery

- **Incomplete or contradictory settings:** recover the board ID from this workflow's prior initialization; ask the user if ambiguous.
- **Referenced board unavailable:** report the problem; get user approval for a replacement.
- **Uncertain creation result:** recover the board ID or confirm creation failed before retrying.
- **Settings save failed:** report the board ID and save error; resume by saving that ID.

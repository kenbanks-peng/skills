# Card format

Use one card per independently finishable outcome. Title it with a verb and observable outcome, such as `Reject expired invitation tokens`. Store priority and deadlines in native fields.

Fill Outcome, Acceptance, and Ownership and next action before execution:

```markdown
## Outcome

<What must change and why; scope boundaries.>

## Acceptance

- [ ] <Observable result>
- [ ] <Required verification>

## Ownership and next action

- Owner: <agent/person, or unassigned>
- Next: <concrete action>

## References

<Specifications, code, and related cards. Omit when unnecessary.>

## Evidence

<Checks, results, and delivered artifacts.>
```

## Related work

- **Completed match:** link new follow-ups; reopen when the original acceptance no longer holds.
- **Shared outcome and owner:** use a `## Steps` checklist for implementation steps.
- **Independent ownership, blocking, or acceptance:** use linked cards identifying each prerequisite result. Confirm prerequisites before starting.

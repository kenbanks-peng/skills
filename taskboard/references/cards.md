# Card format

Use one card per independently finishable outcome. Title it with a verb and observable outcome, such as `Reject expired invitation tokens`. Store priority and deadlines in native fields.

Fill Outcome, Acceptance, and Owner before execution.

**Handoff action** is the concrete starting point for the next agent or session after the current executor has done what it can. Set it as part of moving to Blocked or handing off work, including for review or a session interruption. Include the actor or prerequisite when needed. It stays unchanged during active execution rather than tracking individual implementation steps. Use `None` until a handoff is needed; on completion or cancellation, use `None — complete` or `None — cancelled`.

```markdown
## Outcome

<What must change and why; scope boundaries.>

## Acceptance

- [ ] <Observable result>
- [ ] <Required verification>

## Dependencies

- [ ] <dependency 1>
- [ ] <dependency 2>

## Ownership and handoff

- Owner: <agent/person, or unassigned>
- Handoff action: None

## References

<Specifications, code, urls, etc. Omit when unnecessary.>
<Child card links. Omit when unnecessary.>

## Evidence of done

<Checks, results, and delivered artifacts.>
```

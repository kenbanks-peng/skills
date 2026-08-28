---
name: refactor
description: Refactor code while preserving observable behavior. Use for requests to restructure, simplify, remove duplication, improve maintainability, or clean technical debt without a requested feature change.
---

Refactor the code and verify the result. Optimize for a safer structure with unchanged observable behavior.

1. **Set contract policy first.** Before any other work, ask the user whether backward compatibility is required or contracts can break when needed. Apply that decision to all public APIs, schemas, configuration formats, command interfaces, and other external contracts.

2. **Map the work.** Read the applicable repository instructions, architecture, public contracts, configuration, themes, test setup, and quality commands. Map the file and folder layout. Identify affected behavior, its checks, and debt in file size, module boundaries, folder organization, names, configuration, and themes.

3. **Make the design clear.** State the behavior that must remain stable and the structural problems to remove. Split oversized files into cohesive modules. Give files and folders a clear responsibility. Use precise, domain-based names for variables, functions, types, and modules. Trace callers, tests, data flow, error paths, configuration, themes, and lifecycle boundaries before you move an abstraction.

4. **Refactor completely.** Remove the identified debt across the repository. Prioritize manageable file size, cohesive modules, narrow interfaces, explicit ownership, and a folder layout that makes dependencies and responsibilities clear. Consolidate and correctly locate applicable configuration and theme files. Remove obsolete files and duplicate configuration. Keep each change mechanically safe: make small coherent edits, preserve observable behavior, and update all callers, tests, types, documentation, and tooling that the change affects.

5. **Repair relevant failures.** Treat failures in the affected behavior as part of the work, including failures that existed before the refactor. Diagnose the cause, repair it, and keep the fix within the established contract policy.

6. **Verify in layers.** Run focused tests and static checks first. Then run the repository's broader required checks when feasible. Add or improve focused tests when the existing suite does not protect the behavior you changed.

7. **Report the result.** Give the changed paths, the structural improvements, behavior or contract decisions, and every check run with its result. Clearly state any checks that could not run and the reason.

Completion requires: all identified repository refactoring debt—including file size, module and folder organization, names, configuration, and themes—is addressed or explicitly reported as blocked; affected behavior is protected by relevant checks; required checks pass; and any public-contract policy is confirmed before that contract changes.

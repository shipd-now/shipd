## ADDED Requirements

### Requirement: Traceability tag enforcement
id: traceability-tag-enforcement

The linter SHALL error — not warn — for every checkbox task in a change's
`tasks.md` that lacks a well-formed `[req: ...]` traceability tag, carries more
than one tag, combines the wildcard `*` with requirement ids, or references an
id that does not resolve to a requirement id present in the change's own delta
specs (any operation header, any capability). Each violating task SHALL
produce its own error naming the task's ordinal position.

#### Scenario: Missing tag is an error
- **WHEN** a task line has no `[req: ...]` tag
- **THEN** the linter reports an error for that task and exits non-zero

#### Scenario: Unresolvable id is an error
- **WHEN** a task carries `[req: no-such-requirement]` and no delta spec in
  the change declares that id
- **THEN** the linter reports an error naming the unresolvable id

#### Scenario: Well-tagged change lints clean
- **WHEN** every task carries either resolvable ids or a lone wildcard tag
- **THEN** the linter reports no traceability errors

## MODIFIED Requirements

### Requirement: Task traceability tag enforcement
id: traceability-tag-enforcement
base: 5c16cd83ee32

The linter SHALL error — not warn — for every checkbox task in a change's
`tasks.md` that lacks a well-formed `[req: ...]` traceability tag, carries more
than one tag, combines the wildcard `*` with requirement ids, or references an
id that does not resolve to a requirement id present in the change's own delta
specs (any operation header, any capability). Each violating task SHALL
produce its own error naming the task's ordinal position. A checkbox task is
a line whose content begins — after optional leading blanks — with the
`- [<state>]` marker (state space, `~`, or `x`): the same anchored grammar
the coordinator's ordinal ids count, so a checkbox-shaped literal appearing
mid-line inside a task's wrapped prose SHALL be neither counted as a task nor
required to carry a tag, and the linter's ordinals SHALL always match the
coordinator's.

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

#### Scenario: A checkbox literal in task prose is not a task
- **GIVEN** a tagged task whose wrapped description contains a backticked
  checkbox-marker literal on a continuation line
- **WHEN** the linter runs
- **THEN** no traceability error is reported for the literal, and the
  ordinals in any real errors still name the real tasks

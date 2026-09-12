## MODIFIED Requirements

### Requirement: Delta operation headers
id: delta-operation-headers
base: 484aa62fa084

A delta spec file SHALL express intent using level-2 operation headers only:
`## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`,
and `## RENAMED Requirements`. Requirement blocks under these headers carry the
same `id:` slugs used in the master library. An entry under
`## MODIFIED Requirements` MAY carry one or more `Dropped:` metadata lines,
each naming the exact title of one `#### Scenario:` the entry deliberately
removes from the master requirement it edits. `Dropped:` is delta-only
metadata: the merge engine SHALL NOT write it into the master library, exactly
as it withholds `base:`, `Reason:` and `Migration:`.

#### Scenario: Delta declares intent explicitly
- **WHEN** a change adds one new requirement and edits one existing requirement
- **THEN** the new requirement appears under `## ADDED Requirements` and the
  edited one under `## MODIFIED Requirements`, each with its `id:` slug

#### Scenario: A deliberate scenario removal is named
- **WHEN** a MODIFIED entry deliberately removes two of its base requirement's
  scenarios
- **THEN** the entry carries a `Dropped:` line naming each removed scenario's
  title, and the merged master carries no `Dropped:` line

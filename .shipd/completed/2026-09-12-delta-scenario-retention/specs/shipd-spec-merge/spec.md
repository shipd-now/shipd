## MODIFIED Requirements

### Requirement: MODIFIED operation
id: modified-operation
base: e46d299c194e

For each entry under `## MODIFIED Requirements`, the engine SHALL replace the
matching master requirement's content with the incoming content. If no
requirement with that `id` exists in the master, the engine SHALL insert the
incoming content and emit a warning (take-newer semantics). The engine SHALL
withhold the entry's `Dropped:` metadata from the master it writes, so a
merged master carries only its title, `id:` and content.

#### Scenario: Existing requirement is replaced
- **WHEN** a MODIFIED entry's `id` exists in the master
- **THEN** the master requirement's body and scenarios are replaced by the
  incoming content

#### Scenario: MODIFIED target is missing
- **WHEN** a MODIFIED entry's `id` is absent from the master
- **THEN** the engine inserts the incoming requirement and emits a warning that
  the modified target was not found

#### Scenario: Dropped metadata never reaches the master
- **WHEN** a MODIFIED entry carrying a `Dropped:` line is merged
- **THEN** the rewritten master requirement contains no `Dropped:` line

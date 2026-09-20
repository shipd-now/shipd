## ADDED Requirements

### Requirement: Store-sync check line is report-only
id: doctor-store-sync-line

The `/s:doctor` skill SHALL recognize `store-sync` among the parsed check
names and SHALL treat it as report-only: no remedy row SHALL exist for it,
the skill SHALL never push, pull, or fetch on its behalf, and the line SHALL
be relayed in the diagnosis exactly as the other informational checks are.

#### Scenario: Store-sync line is parsed and never remediated
- **WHEN** the doctor output carries an `ok store-sync — …` line
- **THEN** the skill parses it like any other check line and proposes no
  remedy for it

#### Scenario: An unpushed-commits warning is relayed, not acted on
- **WHEN** the doctor output carries a `warn store-sync — …` line naming
  unpushed commits
- **THEN** the skill relays the line to the user, proposes no remedy of its
  own, and runs no git

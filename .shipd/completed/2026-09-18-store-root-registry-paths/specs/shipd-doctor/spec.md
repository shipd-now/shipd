## ADDED Requirements

### Requirement: Store check line is report-only
id: doctor-store-line

The `/s:doctor` skill SHALL recognize `store` among the parsed check names and
SHALL treat it as report-only: no remedy row SHALL exist for it, the skill SHALL
never move, create, or delete a store directory on its behalf, and the line
SHALL be relayed in the diagnosis exactly as the other informational checks are.

#### Scenario: Store line is parsed and never remediated
- **WHEN** the doctor output carries an `ok store — …` line
- **THEN** the skill parses it like any other check line, proposes no remedy for
  it, and moves nothing

#### Scenario: A stranded-store warning is relayed, not acted on
- **WHEN** the doctor output carries a `warn store — …` line naming a stranded
  basename path and a `git mv` remedy
- **THEN** the skill relays the line and its remedy text to the user and
  proposes no remedy of its own

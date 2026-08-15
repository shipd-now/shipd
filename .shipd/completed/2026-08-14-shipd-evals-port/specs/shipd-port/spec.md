## ADDED Requirements

### Requirement: Eval fixtures sit on the shipd content layout
id: evals-fixture-layout

Every ported eval case's fixture SHALL carry its content directory as `.shipd`,
with the grammar README and the lifecycle subdirectories the source fixture had,
and no fixture SHALL retain a `.am` directory.

#### Scenario: Each fixture carries a shipd content directory
- **WHEN** each ported eval case's fixture is inspected
- **THEN** it contains a `.shipd` directory holding the grammar README and the
  same lifecycle subdirectories as its source fixture

#### Scenario: No fixture keeps the old content directory
- **WHEN** the ported eval tree is searched for a `.am` directory
- **THEN** none is found

### Requirement: The eval runner drives the shipd plugin and namespace
id: evals-runner-namespace

The ported eval runner SHALL launch each headless session against the `plugins/s`
plugin directory, SHALL drive the `/s:plan` skill, and SHALL discover emitted
changes under the `.shipd` content directory in both the scratch root and one
level of worktrees.

#### Scenario: Runner targets the ported plugin and skill
- **WHEN** the ported runner's session launch and prompt are inspected
- **THEN** the plugin directory ends in `plugins/s` and the skill driven is
  `/s:plan`

#### Scenario: Runner discovers changes under the shipd directory
- **WHEN** the ported runner's change-discovery globs are inspected
- **THEN** they resolve under `.shipd/planned/` in the scratch root and under one
  level of worktrees

### Requirement: The ported eval harness passes its own tests and a live run
id: evals-verified-run

The ported eval harness's unit tests SHALL pass without a live session, and a
live eval run SHALL report a passing result for every case.

#### Scenario: Runner unit tests pass offline
- **WHEN** the ported `evals/tests/` suite is run
- **THEN** it reports no failures and no errors, with no session launched

#### Scenario: A live eval run passes
- **WHEN** the ported runner is executed against the shipd repository
- **THEN** every case reports a pass rate of 1.0 and the runner exits `0`

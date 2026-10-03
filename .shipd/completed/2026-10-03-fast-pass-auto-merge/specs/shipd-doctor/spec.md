## ADDED Requirements

### Requirement: Fast-pass check line is report-only
id: doctor-fast-pass-line

The `/s:doctor` skill SHALL recognize `fast-pass` among the parsed check names
and SHALL treat it as report-only: no remedy row SHALL exist for it, the skill
SHALL never set the `SHIPD_FAST_PASS` variable on its behalf, and the line
SHALL be relayed in the diagnosis exactly as the other informational checks
are. Enabling unattended merging is a consented setup step owned by `/s:gate`,
never a repair the preflight proposes.

#### Scenario: Fast-pass line is parsed and never remediated
- **WHEN** the doctor output carries an `ok fast-pass — …` line
- **THEN** the skill parses it like any other check line, proposes no remedy
  for it, and sets no repository variable

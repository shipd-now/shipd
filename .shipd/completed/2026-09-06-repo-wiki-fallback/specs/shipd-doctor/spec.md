## ADDED Requirements

### Requirement: Wiki check line is report-only
id: doctor-wiki-line

The `/s:doctor` skill SHALL recognize `wiki` among the parsed check names
and SHALL treat it as report-only: no remedy row SHALL exist for it, the
skill SHALL never scaffold a wiki store on its behalf, and the line SHALL be
relayed in the diagnosis exactly as the other informational checks are.

#### Scenario: Wiki line is parsed and never remediated
- **WHEN** the doctor output carries an `ok wiki — …` line
- **THEN** the skill parses it like any other check line, proposes no remedy
  for it, and creates no store

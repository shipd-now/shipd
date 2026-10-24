## MODIFIED Requirements

### Requirement: Risk report and plan-deep suggestion
id: epic-grill-risk-report
base: aba011e42084

After the last gate and before the launch preflight, the skill SHALL load
`skills/epic/references/risk-rubric.md` and print one risk table row per
selected member with the columns Member, Code, Integration, Unknowns, Risk,
Novelty, Overall, and Why. The skill SHALL NOT write the scores into any
file. When at least one member's Overall is `medium` or `high`, the skill
SHALL print `/s:plan-deep <epic> <member> ...` naming exactly those members
in table order directly under the table, and SHALL close its whole output,
after the `/s:autopilot` line or the fail list, with the sentence
`There are complex specs worth a deep plan, kick it off with:`, a blank
line, and that same command alone on its own line. When every member is
`low`, the skill SHALL print neither. The skill SHALL NOT run
`/s:plan-deep` itself.

#### Scenario: A medium member earns the suggestion twice
- **GIVEN** a grill whose members `a` and `b` gate to `ready`, scoring `low`
  and `medium`
- **WHEN** the Ending prints
- **THEN** the risk table shows both rows, `/s:plan-deep <epic> b` prints
  under the table, and the output's last line is `/s:plan-deep <epic> b`,
  preceded by the "There are complex specs" sentence and a blank line

#### Scenario: An all-low epic prints no suggestion
- **WHEN** every selected member scores `low`
- **THEN** the risk table prints and no `/s:plan-deep` line appears

#### Scenario: A red preflight still closes on the suggestion
- **GIVEN** a `high` member and a preflight that exits 1
- **WHEN** the Ending prints
- **THEN** the fail lines are listed, no `/s:autopilot` line prints, and the
  output still closes on the `/s:plan-deep` command

#### Scenario: Scores are never persisted
- **WHEN** the risk table prints
- **THEN** no member's `plan.md`, delta spec, or `tasks.md` changes

#### Scenario: The grill reads the rubric from its epic home
- **WHEN** the grill's skill and harness body are read
- **THEN** both cite `skills/epic/references/risk-rubric.md`

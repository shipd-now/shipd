# report-output

### Requirement: Report prints rows sorted by team then name
id: report-row-order

The `report` CLI (`src/report.py`) SHALL print its rows sorted by team
ascending, then by name ascending within each team.

#### Scenario: Rows print in team-then-name order
- **WHEN** `report.py` is run with no arguments
- **THEN** stdout lists rows ordered first by team ascending, then by name
  ascending within a team

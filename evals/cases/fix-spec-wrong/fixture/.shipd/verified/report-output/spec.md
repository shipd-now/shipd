# report-output

### Requirement: Report prints the name column at a fixed width
id: report-column-width

The `report` CLI (`src/report.py`) SHALL print the name column left-justified
to a fixed width of six characters.

#### Scenario: Name column is left-justified to six characters
- **WHEN** `report.py` is run with no arguments
- **THEN** each row's name field is left-justified and padded to exactly six
  characters wide

# reporting

### Requirement: Report prints a fixed table of rows
id: report-prints-a-fixed-table-of-rows

The `report` CLI (`src/report.py`) SHALL print its fixed set of rows to stdout
as a human-readable table. The output SHALL begin with a header line naming the
columns (`name`, `age`, `team`) and SHALL render one row per record with the
columns aligned by fixed-width padding.

#### Scenario: Default invocation prints the aligned table
- **WHEN** `report.py` is run with no arguments
- **THEN** stdout starts with a `name    age  team` header line followed by one
  padded line per record, columns aligned

## ADDED Requirements

### Requirement: Lint JSON output
id: lint-json

`spec_lint.py` SHALL accept a `--json` flag that emits one JSON object on
stdout — `ok` (boolean), `errors` (array of finding strings), and `warnings`
(array of warning strings), carrying the same texts the flagless mode
prints — and nothing else on stdout. The exit code SHALL be identical to
the flagless mode for the same findings, and without the flag the text
output SHALL stay byte-identical.

#### Scenario: A clean lint is machine-readable
- **WHEN** `spec_lint.py --json` runs over a valid library
- **THEN** stdout parses as `{"ok": true, "errors": [], "warnings": [...]}`
  and the exit code is 0

#### Scenario: Findings land in the errors array
- **WHEN** `spec_lint.py <change> --json` runs on a change with a structural
  error
- **THEN** the object's `ok` is false, the error string appears in
  `errors`, and the exit code is nonzero exactly as without the flag

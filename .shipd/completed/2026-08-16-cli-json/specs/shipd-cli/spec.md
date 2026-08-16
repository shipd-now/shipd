## ADDED Requirements

### Requirement: List JSON output
id: list-json

The `shipd list` verb SHALL accept a `--json` flag that emits the listing as
a JSON array on stdout — one object per row with `name`, `location`, and
`status`, in the same order and with the same rows as the text mode,
including the archived rows under `--all` — and nothing else. An empty
listing SHALL emit an empty JSON array. Without the flag the text output
SHALL stay byte-identical, and delegated verbs SHALL keep passing `--json`
through to their engine scripts verbatim.

#### Scenario: List rows are machine-readable
- **WHEN** `shipd list --json` runs in a repo with an in-flight change in a
  worktree
- **THEN** stdout parses as a JSON array whose entry carries the change
  name, its `worktree:<name>` location, and its status

#### Scenario: Empty listing is an empty array
- **WHEN** `shipd list --json` runs with no changes in flight
- **THEN** stdout is an empty JSON array, not the text placeholder

#### Scenario: Delegated verbs pass the flag through
- **WHEN** `shipd epic <slug> --json` runs
- **THEN** the output is exactly `spec_status.py epic-show <slug> --json`'s
  output

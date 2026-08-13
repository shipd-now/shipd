## ADDED Requirements

### Requirement: Workspace sync verb
id: workspace-sync-verb

The status CLI SHALL provide `workspace-sync` printing the engine's
materialization plan as one keyed block per member (`member:`, `path:`,
`state:`, `action:`, plus `source:`, `url:`, `command:`, and `drift:` when
applicable) followed by a `gitignore:` section, and SHALL support `--json`
emitting one JSON object per record with a `kind` field
(`member`/`gitignore`). A computed plan SHALL exit zero regardless of drift
or unmaterializable entries. With `--write-gitignore` the verb SHALL
additionally rewrite only the marked member-repos block to match the
manifest's member paths, idempotently; without the flag it SHALL write
nothing. The verb SHALL require a discoverable workspace and SHALL exit
non-zero printing the findings when the registry fails validation.

#### Scenario: Plan prints and exits zero
- **GIVEN** a workspace whose manifest has one present member and one
  absent member with a url
- **WHEN** `workspace-sync` runs
- **THEN** two keyed member blocks and a gitignore section print and the
  exit code is zero

#### Scenario: JSON mode emits parseable records
- **WHEN** `workspace-sync --json` runs in that workspace
- **THEN** every output line parses as a JSON object carrying a `kind`
  field

#### Scenario: Gitignore write is opt-in and scoped
- **GIVEN** a marked member block missing a manifest path
- **WHEN** `workspace-sync` runs without and then with `--write-gitignore`
- **THEN** the first run leaves `.gitignore` unchanged and the second
  rewrites only the marked block to include the path, leaving content
  outside the markers untouched

#### Scenario: Invalid registry gates the verb
- **WHEN** `workspace-sync` runs where the registry declares a malformed
  project entry
- **THEN** the CLI exits non-zero printing the validation findings

#### Scenario: No workspace errors
- **WHEN** `workspace-sync` runs with no discoverable workspace
- **THEN** the CLI exits non-zero saying no workspace was found

## ADDED Requirements

### Requirement: Workspace root discovery
id: workspace-root-discovery

The engine SHALL locate the workspace root by upward search: starting from a
given directory and walking parent-by-parent to the filesystem root, the
nearest directory containing `.shipd/workspace.json` SHALL be the
workspace root, the starting directory itself included. If no ancestor
carries the marker, the search SHALL report that no workspace exists rather
than erroring. The search SHALL NOT require the starting directory or the
workspace root to be a git repository.

#### Scenario: Nearest ancestor wins
- **GIVEN** a marker at `/ws/.shipd/workspace.json` and another at
  `/ws/nested/.shipd/workspace.json`
- **WHEN** discovery starts from `/ws/nested/repo`
- **THEN** the workspace root resolved is `/ws/nested`

#### Scenario: No marker means no workspace
- **WHEN** discovery starts from a directory with no marker in any ancestor
- **THEN** the search returns no workspace root and raises no error

#### Scenario: The starting directory can be the root
- **WHEN** discovery starts from a directory that itself contains
  `.shipd/workspace.json`
- **THEN** that directory is the workspace root

### Requirement: Workspace registry loading
id: workspace-registry-loading

The engine SHALL load a workspace's registry from
`<workspace-root>/.shipd/workspace.json` using the standard-library JSON
parser and SHALL return its top-level object as parsed, preserving unknown
keys for forward compatibility. If the file is missing, is not parseable
JSON, or its top level is not an object, the engine SHALL raise a clear
error naming the file. The registry loader SHALL NOT interpret or validate
project entries — project semantics belong to a later change.

#### Scenario: Registry loads as a tolerant dict
- **GIVEN** a registry containing `projects` plus an unrecognized
  `future-key` entry
- **WHEN** the registry is loaded
- **THEN** the returned object carries both keys unchanged

#### Scenario: Malformed registry errors clearly
- **WHEN** the registry file contains invalid JSON
- **THEN** loading raises an error naming `.shipd/workspace.json`

#### Scenario: Non-object top level errors
- **WHEN** the registry file parses to a JSON array
- **THEN** loading raises an error naming the file

## MODIFIED Requirements

### Requirement: Layout init verb
id: layout-init-verb
base: f6f4ac9dd716

The status CLI SHALL provide an `init` verb that resolves the content
directory from the root's layered configuration and creates the `verified/`,
`planned/`, `completed/`, and `research/` directories under it — creating the
content directory itself and any missing parents — without modifying or
removing anything that already exists. For each of the four directories the
verb SHALL print one line, `created <path>/` when it made the directory and
`exists <path>/` when it was already a directory (`<path>` relative to the
root), followed by the summary line `all shipd directories are ready`, and
SHALL exit `0` whether it created all, some, or none of them. If the content
directory or any of the four targets exists as a non-directory, the verb
SHALL create nothing, report the offending path via the standard `Error:`
convention, and exit non-zero.

#### Scenario: Fresh repository gets the full layout
- **WHEN** `spec_status.py init --root <dir>` runs against a directory with
  no content directory
- **THEN** `<dir>/.shipd/verified`, `<dir>/.shipd/planned`,
  `<dir>/.shipd/completed`, and `<dir>/.shipd/research` exist afterward, each
  is reported `created`, and the run exits `0` ending with
  `all shipd directories are ready`

#### Scenario: Existing content is never clobbered
- **WHEN** `init` runs against a root whose `verified/` already holds a
  capability spec and whose `research/` already holds a report while
  `planned/` and `completed/` are missing
- **THEN** the existing spec and report files are untouched, `verified` and
  `research` are reported `exists`, the two missing directories are reported
  `created`, and the run exits `0`

#### Scenario: Idempotent re-run
- **WHEN** `init` runs a second time against an already-initialized root
- **THEN** all four directories are reported `exists` and the run still
  exits `0` with the ready summary

#### Scenario: Non-directory blocker refuses
- **WHEN** a regular file occupies the content-directory path or one of the
  four target paths
- **THEN** the verb creates no directory, prints an `Error:` line naming the
  offending path, and exits non-zero

#### Scenario: Configured content directory is honored
- **WHEN** the root's configuration declares `"dir": "specs"` and `init` runs
- **THEN** the layout is created under `specs/`, not `.shipd/`

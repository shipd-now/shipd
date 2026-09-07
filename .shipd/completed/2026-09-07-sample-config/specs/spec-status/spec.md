## MODIFIED Requirements

### Requirement: Layout init verb
id: layout-init-verb
base: e61a601ec1c8

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

The verb SHALL additionally install the plugin's copyable config example —
located relative to the engine's own scripts directory at
`../references/shipd.config.example.json`, so the same resolution holds in a
repo checkout and in the plugin cache snapshot — as
`<content-dir>/shipd.config.example.json`, and SHALL report it with one
`created <path>` / `exists <path>` line (no trailing separator) printed after
the four directory lines and before the summary line. The verb SHALL write
the file only when nothing exists at the destination path: while any
filesystem object is present there, the verb SHALL leave it byte-for-byte
untouched and report `exists`. If the source reference file is missing, then
the verb SHALL print one warning line to stderr naming the probed source path,
SHALL skip the installation, and SHALL leave its exit code unchanged.

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

#### Scenario: Fresh init installs the config sample
- **WHEN** `init` runs against a root with no content directory
- **THEN** `<content-dir>/shipd.config.example.json` exists afterward with
  content identical to the plugin's reference file, and the run reports it
  `created` between the directory lines and the summary

#### Scenario: An existing sample copy is never rewritten
- **GIVEN** a root whose `<content-dir>/shipd.config.example.json` holds
  user-modified content
- **WHEN** `init` re-runs
- **THEN** the file's content is byte-for-byte unchanged and the run reports
  it `exists`

#### Scenario: Missing reference warns without failing
- **GIVEN** an engine whose `../references/shipd.config.example.json` is
  absent
- **WHEN** `init` runs against a fresh root
- **THEN** the four directories are still created, one stderr warning names
  the probed source path, no sample file is installed, and the run exits `0`

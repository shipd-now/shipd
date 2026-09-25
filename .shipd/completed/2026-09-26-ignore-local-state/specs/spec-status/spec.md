## MODIFIED Requirements

### Requirement: Layout init verb
id: layout-init-verb
base: 11578bc7ec66

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

The verb SHALL additionally seed the two local-state ignore rules —
`<content-dir>/state.json` and `<content-dir>/autopilot/`, each relative to
the root — into the root's `.gitignore`, appending only a rule that is absent
and creating the file when it does not exist, and SHALL report each rule with
one `ignored <rule>` line when appended or `exists <rule>` line when already
present, printed after the config-sample line and before the summary line.
While the root is a git checkout and either path is tracked by git, the verb
SHALL untrack it from the index without deleting it from disk and SHALL print
one `untracked <path>` line per path after the rule lines. If the content
directory resolves outside the root, then the verb SHALL print no rule line
and touch no `.gitignore`. If `git` is unavailable or the root is not a
checkout, then the verb SHALL still seed the rules and skip the untrack step,
leaving its exit code unchanged.

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

#### Scenario: Fresh init seeds the ignore rules
- **WHEN** `init` runs against a fresh root with no `.gitignore`
- **THEN** `.gitignore` is created carrying `.shipd/state.json` and
  `.shipd/autopilot/`, and the run prints `ignored .shipd/state.json` and
  `ignored .shipd/autopilot/` after the config-sample line and before the
  summary

#### Scenario: Re-run reports present rules
- **WHEN** `init` re-runs against a root whose `.gitignore` already carries
  both rules
- **THEN** `.gitignore` is byte-for-byte unchanged and each rule is reported
  `exists`

#### Scenario: A tracked state file is untracked by init
- **GIVEN** a git checkout whose committed tree tracks `.shipd/state.json`
  and `.shipd/autopilot/demo-build-heartbeat.json`
- **WHEN** `init` runs
- **THEN** `git ls-files .shipd` lists neither path afterwards, both files
  still exist on disk, and the run prints one `untracked <path>` line per
  path before the summary

#### Scenario: Configured content directory names the rules
- **WHEN** the root's configuration declares `"dir": "specs"` and `init` runs
- **THEN** the seeded rules are `specs/state.json` and `specs/autopilot/`

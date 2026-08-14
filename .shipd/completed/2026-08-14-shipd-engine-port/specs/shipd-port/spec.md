## ADDED Requirements

### Requirement: Ported engine carries shipd namespace constants
id: engine-namespace-constants

The ported engine under `plugins/s/` SHALL resolve its configuration filename as
`.shipd-config.json`, its default content directory as `.shipd`, its default
personal memory store as `~/.shipd-memory`, its default build log directory as
`~/.shipd/builds`, its tui virtualenv cache under a `shipd` directory, and its
worktree idle-window environment variable as `SHIPD_WORKTREE_IDLE_MINUTES`. No
engine script SHALL reference `.shipd-config.json`, `~/.shipd-memory`, `~/.shipd/builds`,
or `SHIPD_WORKTREE_IDLE_MINUTES`.

#### Scenario: Config resolution uses the shipd filename
- **WHEN** `spec_common.CONFIG_FILENAME` and `spec_common.DEFAULT_DIR` are read
  from the ported engine
- **THEN** they are `.shipd-config.json` and `.shipd`

#### Scenario: Machine-level paths are namespaced to shipd
- **WHEN** the ported `spec_common.DEFAULT_MEMORY_DIR`, `metrics.DEFAULT_LOG_DIR`,
  and the `tui_bootstrap` venv cache path are read
- **THEN** they are `~/.shipd-memory`, `~/.shipd/builds`, and a path containing
  `shipd/tui-venv`

#### Scenario: No am-namespaced constant survives
- **WHEN** the ported `plugins/s/` tree is searched for `.shipd-config.json`,
  `~/.shipd-memory`, `~/.shipd/builds`, and `SHIPD_WORKTREE_IDLE_MINUTES`
- **THEN** no match is found

### Requirement: Ported engine suites pass under the new paths
id: engine-suites-green

All four ported test suites — the engine suite, the textual suite, the review
suite, and the video-ingest suite — SHALL pass when discovered under their
`plugins/s/` paths.

#### Scenario: Engine suite passes
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/build/tests` runs in
  the shipd repo
- **THEN** it reports no failures and no errors

#### Scenario: Every suite passes
- **WHEN** the textual, review, and video-ingest suites are each discovered under
  their `plugins/s/skills/…/tests` paths and run
- **THEN** each reports no failures and no errors

### Requirement: Shipd CI runs the ported suites
id: engine-ci-workflow

The shipd repository SHALL carry a `ci` workflow that runs each of the four
ported test suites and both spec-lint steps, with every discovery path resolving
to a directory that exists in the shipd tree.

#### Scenario: Workflow paths resolve
- **WHEN** each `discover -s <path>` and script path in
  `.github/workflows/ci.yml` is checked against the shipd tree
- **THEN** every one of them exists

#### Scenario: Suite steps are green on the port commit
- **WHEN** the `ci` workflow runs on the port commit
- **THEN** all four unittest steps report success

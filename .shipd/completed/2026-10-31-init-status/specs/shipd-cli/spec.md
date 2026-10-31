## ADDED Requirements

### Requirement: Init status mode
id: cli-init-status-mode

When invoked as `shipd init`, the binary SHALL select the delegate by the
first trailing argument: the bare word `status` SHALL be consumed and delegate
to `spec_status.py init-status`, and any other first trailing argument (or
none) SHALL delegate to `spec_status.py init` with all trailing arguments
intact, so every existing `shipd init` invocation behaves exactly as before.
The delegation SHALL replace the binary's process like every other delegated
verb, so the delegate's output and exit code are the binary's own. The usage
banner SHALL name the mode as `init [status] [--root DIR]` and say that
`status` reports `first-run`, `layout-missing`, or `ready`.

#### Scenario: The status word reaches the verdict verb
- **GIVEN** a directory with no `.shipd-config.json` and no `.shipd/`
- **WHEN** `shipd init status --root <dir>` runs
- **THEN** it prints `verdict: first-run` and exits `0`, and nothing is
  created under the directory

#### Scenario: Plain init is unchanged
- **WHEN** `shipd init --root <dir>` runs on an empty directory
- **THEN** it creates the layout and prints `all shipd directories are ready`,
  exactly as `spec_status.py init --root <dir>` does

#### Scenario: The mode table maps both words
- **WHEN** the binary's init mode table is read
- **THEN** it maps no word to `spec_status.py init` and `status` to
  `spec_status.py init-status`

#### Scenario: The banner names the status mode
- **WHEN** `shipd help` runs
- **THEN** the banner carries `init [status] [--root DIR]`

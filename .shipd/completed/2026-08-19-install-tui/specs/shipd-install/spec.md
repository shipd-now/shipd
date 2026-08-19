## MODIFIED Requirements

### Requirement: One-command install script
id: install-script
base: 0998b7712bac

A repo-root `install.sh` SHALL, when run on a machine with the `claude` CLI
and `python3` present: register the `shipd-now/shipd` GitHub marketplace via
`claude plugin marketplace add`, install the plugin via
`claude plugin install s@shipd`, write the version-independent `shipd`
launcher to `~/.local/bin/shipd` marked executable, and print a PATH hint
when `~/.local/bin` is not on the invoking PATH. After a successful
install, the script SHALL print an auto-update notice naming the
per-marketplace enable surfaces — the `/plugin` → Marketplaces toggle for
`shipd` and the `"autoUpdate": true` settings entry — and the apply
semantics (updates land after session start and activate at the next
launch), while never editing any settings file itself. Where a controlling
terminal is available (`/dev/tty` opens read-write), the script SHALL then
run the just-written launcher's `install` verb with its input and output
bound to `/dev/tty`, fail-soft: a nonzero exit from that step SHALL print
one note and SHALL NOT fail the installer. Where no controlling terminal is
available, the script SHALL skip that step and its output SHALL remain
unchanged. If `claude` or `python3` is
missing, then the script SHALL exit nonzero with a single actionable error
line and change nothing. The script SHALL treat an already-registered
marketplace or already-installed plugin as success (idempotent re-run) and
SHALL download nothing itself beyond what the `claude` CLI performs.

#### Scenario: Fresh install performs both claude steps and writes the launcher
- **WHEN** `install.sh` runs with a stub `claude` on PATH and a temp HOME
- **THEN** `claude plugin marketplace add shipd-now/shipd` and
  `claude plugin install s@shipd` are invoked, and an executable
  `~/.local/bin/shipd` exists afterwards

#### Scenario: Missing claude CLI aborts cleanly
- **WHEN** `install.sh` runs with no `claude` on PATH
- **THEN** it exits nonzero with an actionable error and writes no launcher

#### Scenario: Re-run is idempotent
- **WHEN** `install.sh` runs a second time with the marketplace and plugin
  already present
- **THEN** it exits 0 and the launcher is still in place

#### Scenario: Success prints the auto-update notice
- **WHEN** `install.sh` completes successfully
- **THEN** stdout carries the auto-update notice naming the `/plugin`
  marketplace toggle and the `"autoUpdate": true` settings alternative,
  and no settings file was created or modified

#### Scenario: Aborts print no auto-update notice
- **WHEN** `install.sh` aborts on a missing prerequisite
- **THEN** the auto-update notice is absent from the output

#### Scenario: Headless runs skip the interactive finish unchanged
- **WHEN** `install.sh` runs to success with no usable `/dev/tty`
- **THEN** the launcher's `install` verb is not invoked, the script exits
  0, and the output matches the pre-existing success output

#### Scenario: A failing interactive finish never fails the installer
- **WHEN** the guarded step runs and the launcher's `install` verb exits
  nonzero
- **THEN** the script prints one note about the skipped finish and still
  exits 0

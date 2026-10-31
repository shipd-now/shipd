## ADDED Requirements

### Requirement: Config mode words
id: cli-config-modes

When invoked as `shipd config`, the binary SHALL select the delegate by the
first trailing argument: the bare word `set` SHALL be consumed and delegate to
`spec_status.py config-set`, `unset` to `spec_status.py config-unset`, and
`check` to `spec_status.py config-check`, and any other first trailing argument
(or none) SHALL delegate to `spec_status.py config-show` with all trailing
arguments intact, as `cli-dispatch` already maps it. The usage banner SHALL
list the verb as `config [set|unset|check]`.

#### Scenario: Config set mode
- **WHEN** `shipd config set --help` runs
- **THEN** the output is identical to `spec_status.py config-set --help` and
  the exit code is 0

#### Scenario: Config check mode
- **WHEN** `shipd config check --help` runs
- **THEN** the output is identical to `spec_status.py config-check --help` and
  the exit code is 0

#### Scenario: Bare config is still the report
- **WHEN** `shipd config` runs from a repo root
- **THEN** the `config-show` report is printed and the exit code is 0

### Requirement: Doctor config check uses the registry
id: doctor-config-registry-check

The doctor's `config` check SHALL run the same validation as `config-check`
over every declared key in every layer. Where any error is found, the check
SHALL fail carrying the first error's message, followed by `(+<n> more — run
shipd config check)` when there are more. Where only warnings are found, the
check SHALL warn carrying the first warning's message. The existing outcomes
SHALL otherwise hold: a malformed file fails naming it, a `workspaces_root`
naming a missing directory warns, and a clean config reports the content
directory as before. The doctor's remedy text for `config` SHALL name `shipd
config set` and `shipd config unset`.

#### Scenario: A bad pr-mode fails the check
- **GIVEN** a repo layer declaring `"pr-mode": "always"`
- **WHEN** the doctor's `config` check runs
- **THEN** it fails and its detail names `pr-mode`

#### Scenario: An unknown key warns
- **GIVEN** a repo layer declaring `"vioce": false`
- **WHEN** the doctor's `config` check runs
- **THEN** it warns and its detail names `vioce`

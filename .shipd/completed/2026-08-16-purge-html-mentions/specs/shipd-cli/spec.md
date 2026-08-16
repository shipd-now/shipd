## MODIFIED Requirements

### Requirement: Curated verb dispatch
id: cli-dispatch
base: 3da395f81af1

The `shipd` binary SHALL expose exactly the curated verbs `list`, `status`,
`locate`, `epic`, `workspace`, `board`, `metrics`, `lint`, and `doctor`, and
for every verb except `list` and `doctor` SHALL delegate by replacing its
own process with the
mapped engine script invocation (`status` → `spec_status.py show`, `locate` →
`spec_status.py locate`, `epic` → `spec_status.py epic-show`, `workspace` →
`spec_status.py workspace-show`, `board` → `dashboard.py` per the board-mode
mapping below, `metrics` → `metrics.py`, `lint` → `spec_lint.py`), passing
all trailing arguments through verbatim so the delegate's output and exit
code are the binary's own. When `metrics` is given no trailing arguments,
the binary SHALL delegate to `metrics.py summary`. When invoked as
`shipd board`, the binary SHALL select the delegate by the first trailing
argument: the bare word `text` SHALL be consumed and delegate to
`dashboard.py board`, and any other first trailing argument (or none) SHALL
delegate to `dashboard.py tui` with all trailing arguments intact. The
binary SHALL resolve the engine scripts relative to its own resolved file
location. If the verb is unknown or missing — including the retired `tui` —
the binary SHALL print a usage banner listing the curated verbs to stderr
and exit `2`; when invoked with `help`, `-h`, or `--help` it SHALL print the
same banner to stdout and exit `0`.

#### Scenario: Delegated verb preserves output and exit code
- **WHEN** `shipd locate no-such-change` runs in a repo where that change does
  not exist
- **THEN** the binary exits `1` with `Error: change 'no-such-change' not found`
  on stderr, exactly as `spec_status.py locate` does

#### Scenario: Bare board is the interactive board
- **WHEN** `shipd board --help` runs
- **THEN** the output is identical to `dashboard.py tui --help` and the exit
  code is `0`, proving flags pass to the interactive delegate untouched

#### Scenario: Board text mode
- **WHEN** `shipd board text --root <repo>` runs against a repo with an epic
- **THEN** the output of `dashboard.py board --root <repo>` is printed and the
  exit code is `0`

#### Scenario: Unknown board mode word falls through to the interactive delegate
- **WHEN** `shipd board frobnicate --once` runs
- **THEN** the arguments delegate to `dashboard.py tui`, which rejects them as
  unrecognized and exits `2`

#### Scenario: Retired tui verb is a usage error
- **WHEN** `shipd tui` runs
- **THEN** the usage banner is printed to stderr and the binary exits `2`

#### Scenario: Unknown verb is a usage error
- **WHEN** `shipd frobnicate` runs
- **THEN** a usage banner naming the curated verbs is printed to stderr and the
  binary exits `2`

#### Scenario: Help exits zero
- **WHEN** `shipd --help` runs
- **THEN** the usage banner is printed to stdout and the binary exits `0`

#### Scenario: Doctor is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `doctor` among the verbs

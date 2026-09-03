## MODIFIED Requirements

### Requirement: Curated verb dispatch
id: cli-dispatch
base: 4235f473aa5b

The `shipd` binary SHALL expose exactly the curated verbs `init`, `list`,
`status`, `locate`, `related`, `epic`, `workspace`, `board`, `metrics`,
`lint`, `worktree`, `doctor`, `statusline`, `copilot`, `vendor`, `harness`,
`install`, and `update`, and for every verb except `list`, `doctor`,
`statusline`, `copilot`, `vendor`, `harness`, `install`, and `update` SHALL
delegate by replacing its own process with the mapped engine script invocation
(`init` -> `spec_status.py init`, `status` -> `spec_status.py show`, `locate`
-> `spec_status.py locate`, `related` -> `spec_status.py related`, `epic` ->
`spec_status.py epic-show`, `workspace` -> `spec_status.py workspace-show`,
`board` -> `dashboard.py` per the board-mode mapping below, `metrics` ->
`metrics.py`, `lint` -> `spec_lint.py`, `worktree` -> `worktree.py`), passing
all trailing arguments through verbatim so the delegate's output and exit
code are the binary's own. When `metrics` is given no trailing arguments, the
binary SHALL delegate to `metrics.py summary`. When invoked as `shipd board`,
the binary SHALL select the delegate by the first trailing argument: the bare
word `text` SHALL be consumed and delegate to `dashboard.py board`, and any
other first trailing argument (or none) SHALL delegate to `dashboard.py tui`
with all trailing arguments intact. The binary SHALL resolve the engine
scripts relative to its own resolved file location. If the verb is unknown or
missing — including the retired `tui` — the binary SHALL print a usage banner
listing the curated verbs to stderr and exit `2`; when invoked with `help`,
`-h`, or `--help` it SHALL print the same banner to stdout and exit `0`.

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

#### Scenario: Statusline is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `statusline` among the verbs

#### Scenario: Copilot is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `copilot` among the verbs

#### Scenario: Vendor is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `vendor` among the verbs

#### Scenario: Harness is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `harness` among the verbs

#### Scenario: Install is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `install` among the verbs

#### Scenario: Update is an in-binary curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `update` among the verbs, and `update` is
  absent from the delegating verb table, so no engine script is executed for it

#### Scenario: Related is a curated verb that delegates
- **WHEN** `shipd related zzz-no-such-term` runs from a repo whose spec
  library contains no such term
- **THEN** the banner of `shipd --help` lists `related` among the verbs, and
  the invocation exits non-zero with the `Error:` line of
  `spec_status.py related`, proving the delegation

#### Scenario: Init is a curated verb that delegates
- **WHEN** `shipd init --root <dir>` runs against a directory with no content
  directory
- **THEN** the banner of `shipd --help` lists `init` among the verbs, and the
  invocation creates the layout and exits `0` printing the
  `all shipd directories are ready` summary of `spec_status.py init`, proving
  the delegation

#### Scenario: Worktree is a curated verb that delegates
- **WHEN** `shipd worktree` runs with no trailing arguments
- **THEN** the banner of `shipd --help` lists `worktree` among the verbs, and
  the invocation prints `worktree.py`'s own usage — not the shipd banner —
  and exits non-zero, proving the delegation

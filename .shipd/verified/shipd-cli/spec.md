# shipd-cli

### Requirement: Curated verb dispatch
id: cli-dispatch

The `shipd` binary SHALL expose exactly the curated verbs `list`, `status`,
`locate`, `epic`, `workspace`, `board`, `tui`, `metrics`, and `lint`, and for
every verb except `list` SHALL delegate by replacing its own process with the
mapped engine script invocation (`status` → `spec_status.py show`, `locate` →
`spec_status.py locate`, `epic` → `spec_status.py epic-show`, `workspace` →
`spec_status.py workspace-show`, `board` → `dashboard.py board`, `tui` →
`dashboard.py tui`, `metrics` → `metrics.py`, `lint` → `spec_lint.py`),
passing all trailing arguments through verbatim so the delegate's output and
exit code are the binary's own. When `metrics` is given no trailing
arguments, the binary SHALL delegate to `metrics.py summary`. The binary
SHALL resolve the engine scripts relative to its own resolved file location.
If the verb is unknown or missing, the binary SHALL print a usage banner
listing the curated verbs to stderr and exit `2`; when invoked with `help`,
`-h`, or `--help` it SHALL print the same banner to stdout and exit `0`.

#### Scenario: Delegated verb preserves output and exit code
- **WHEN** `shipd locate no-such-change` runs in a repo where that change does
  not exist
- **THEN** the binary exits `1` with `Error: change 'no-such-change' not found`
  on stderr, exactly as `spec_status.py locate` does

#### Scenario: Board delegation
- **WHEN** `shipd board --root <repo>` runs against a repo with an epic
- **THEN** the delivery board output of `dashboard.py board --root <repo>` is
  printed and the exit code is `0`

#### Scenario: Unknown verb is a usage error
- **WHEN** `shipd frobnicate` runs
- **THEN** a usage banner naming the curated verbs is printed to stderr and the
  binary exits `2`

#### Scenario: Help exits zero
- **WHEN** `shipd --help` runs
- **THEN** the usage banner is printed to stdout and the binary exits `0`

### Requirement: List in-flight changes
id: cli-list

When invoked as `shipd list`, the binary SHALL enumerate in-flight changes by
probing the invocation root's `<content-dir>/planned/` and, for each
`.worktrees/<name>` directory that has a `<content-dir>/planned/`, that
worktree's planned changes, printing one line per change with the change
name, its location (`root` or `worktree:<name>`), and its lifecycle status as
read by the engine's status reader. The binary SHALL dedupe by change name
with the worktree occurrence winning. The binary SHALL exclude completed
changes unless `--all` is given, in which case entries from
`<content-dir>/completed/` are appended with status `archived`. If no
in-flight change exists, the binary SHALL print `no changes in flight` and
exit `0`.

#### Scenario: Worktree change is listed with its status
- **WHEN** `shipd list --root <repo>` runs and `<repo>/.worktrees/foo` holds a
  planned change `foo` with `Status: ready`
- **THEN** the output contains one line naming `foo`, `worktree:foo`, and
  `ready`

#### Scenario: Duplicate change deduped, worktree wins
- **WHEN** a change `foo` exists under both the root's `planned/` and
  `.worktrees/foo`'s `planned/` and `shipd list --root <repo>` runs
- **THEN** exactly one `foo` line is printed and its location is
  `worktree:foo`

#### Scenario: Completed changes only under --all
- **WHEN** `<content-dir>/completed/` holds an archived change and
  `shipd list --root <repo>` runs without and then with `--all`
- **THEN** the archived entry appears only in the `--all` output, with status
  `archived`

#### Scenario: Empty tree
- **WHEN** `shipd list --root <repo>` runs against a repo with no planned
  changes and no worktrees
- **THEN** the binary prints `no changes in flight` and exits `0`

### Requirement: Version from the plugin manifest
id: cli-version

When invoked as `shipd --version`, the binary SHALL print the `version` value
read from the `.claude-plugin/plugin.json` adjacent to its own resolved
location and exit `0`. If that manifest is missing or unreadable, the binary
SHALL print `Error: ` and a reason on stderr and exit `1`.

#### Scenario: Version is printed
- **WHEN** `shipd --version` runs from the repo checkout
- **THEN** the version string from `plugins/s/.claude-plugin/plugin.json` is
  printed to stdout and the exit code is `0`

# shipd-cli

### Requirement: Curated verb dispatch
id: cli-dispatch

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

### Requirement: Doctor preflight verb
id: doctor-verb

The `shipd` binary SHALL provide a read-only `doctor` verb that runs
environment preflight checks and prints one `ok <check> — <detail>`,
`warn <check> — <detail>`, or `fail <check> — <detail>` line per check
followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line, and
SHALL exit `1` if any required check fails and `0` otherwise. The required
checks SHALL be: `python` (interpreter at least 3.9), `git` (present on
PATH), and `config` (a resolvable layered configuration at the working
directory; a missing content directory is reported `ok` with a note). The
warning checks — never affecting the exit code — SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `textual` (importable), and
`snapshot` (when the binary runs from a plugin cache snapshot that is not
the newest version directory in the cache; when the binary runs from a
repository checkout, the check SHALL report dev mode as `ok`). The verb
SHALL mutate nothing.

#### Scenario: Healthy environment reports ok
- **WHEN** `shipd doctor` runs with python >= 3.9, git present, a resolvable
  config, gh authenticated, and the newest snapshot
- **THEN** every line begins `ok` and the closing line is `doctor: ok` with
  exit code `0`

#### Scenario: Missing git fails the preflight
- **WHEN** `shipd doctor` runs with no `git` on PATH
- **THEN** a `fail git — ` line with an actionable hint is printed and the
  exit code is `1`

#### Scenario: Unauthenticated gh only warns
- **WHEN** `shipd doctor` runs with `gh` absent or `gh auth status` failing,
  all required checks passing
- **THEN** a `warn gh — ` line is printed and the exit code is `0`

#### Scenario: Missing textual only warns
- **WHEN** `shipd doctor` runs without `textual` importable, all required
  checks passing
- **THEN** a `warn textual — ` line names the board as the only affected
  surface and the exit code is `0`

#### Scenario: Stale snapshot warns
- **WHEN** `shipd doctor` runs from a cache snapshot directory that is not
  the newest version in the cache
- **THEN** a `warn snapshot — ` line names the newer version and the exit
  code is `0`

#### Scenario: Checkout run reports dev mode
- **WHEN** `shipd doctor` runs from a repository checkout rather than a
  cache snapshot
- **THEN** the `snapshot` check reports `ok` with a dev-mode note

### Requirement: List JSON output
id: list-json

The `shipd list` verb SHALL accept a `--json` flag that emits the listing as
a JSON array on stdout — one object per row with `name`, `location`, and
`status`, in the same order and with the same rows as the text mode,
including the archived rows under `--all` — and nothing else. An empty
listing SHALL emit an empty JSON array. Without the flag the text output
SHALL stay byte-identical, and delegated verbs SHALL keep passing `--json`
through to their engine scripts verbatim.

#### Scenario: List rows are machine-readable
- **WHEN** `shipd list --json` runs in a repo with an in-flight change in a
  worktree
- **THEN** stdout parses as a JSON array whose entry carries the change
  name, its `worktree:<name>` location, and its status

#### Scenario: Empty listing is an empty array
- **WHEN** `shipd list --json` runs with no changes in flight
- **THEN** stdout is an empty JSON array, not the text placeholder

#### Scenario: Delegated verbs pass the flag through
- **WHEN** `shipd epic <slug> --json` runs
- **THEN** the output is exactly `spec_status.py epic-show <slug> --json`'s
  output

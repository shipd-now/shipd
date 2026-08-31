## ADDED Requirements

### Requirement: Update verb
id: cli-update

When invoked as `shipd update`, the binary SHALL compare the newest installed
plugin snapshot against the version the registered `shipd` marketplace
publishes and, unless `--check` is given, install a newer published version
through the `claude` CLI.

The binary SHALL resolve the **installed** version as the newest version-named
directory under the cache root — the `SHIPD_PLUGIN_CACHE` environment variable
when set, otherwise `~/.claude/plugins/cache/shipd/s` — by the same
dotted-integer ordering the launcher uses. The binary SHALL resolve the
**available** version by reading the `shipd` entry's `installLocation` from
`~/.claude/plugins/known_marketplaces.json`, refreshing that marketplace with
`claude plugin marketplace update shipd` under a bounded timeout, and then
reading the version declared by the plugin manifest of the marketplace
manifest's `s` entry (its relative-path `source`, resolved against the
install location).

Where the available version is newer than the installed one and `--check` is
absent, the binary SHALL run `claude plugin update s@shipd`, print that
command's captured stdout, re-resolve the newest installed snapshot, and
report the resulting version together with a note that a new session is needed
to load it. Where `--check` is given, the binary SHALL report the pending
update and SHALL run no `claude plugin update`. Where the available version is
not newer, the binary SHALL report that the installed version is the newest
published one and change nothing. Each of these paths SHALL exit `0`.

If `claude` is not on PATH, the `shipd` marketplace is not registered, the
marketplace refresh exits nonzero or times out, the marketplace's manifests
cannot be read or declare no `s` entry with a relative-path `source`, no
installed snapshot exists under the cache root, or `claude plugin update`
exits nonzero, then the binary SHALL report a single `Error:` line on stderr
naming the actionable fix and exit `1`, having installed nothing.

#### Scenario: A newer published version is installed
- **GIVEN** a cache root whose newest snapshot is `0.6.9` and a registered
  marketplace publishing `0.6.10`
- **WHEN** `shipd update` runs
- **THEN** `claude plugin update s@shipd` is invoked, and stdout reports the
  update from `0.6.9` to `0.6.10` and the need to start a new session to load
  it, and the exit code is `0`

#### Scenario: Check mode reports without installing
- **GIVEN** the same cache root and marketplace
- **WHEN** `shipd update --check` runs
- **THEN** stdout reports that `0.6.10` is available, no `claude plugin update`
  is invoked, and the exit code is `0`

#### Scenario: Already current changes nothing
- **GIVEN** a cache root whose newest snapshot is `0.6.10` and a marketplace
  publishing `0.6.10`
- **WHEN** `shipd update` runs
- **THEN** stdout reports that `0.6.10` is the newest published version, no
  `claude plugin update` is invoked, and the exit code is `0`

#### Scenario: Newest snapshot wins numerically
- **GIVEN** cache version directories `0.6.9` and `0.6.10`
- **WHEN** the installed version is resolved
- **THEN** it is `0.6.10`, not the lexicographically larger `0.6.9`

#### Scenario: An unregistered marketplace is an actionable error
- **WHEN** `shipd update` runs with no `shipd` entry in
  `known_marketplaces.json`
- **THEN** a single `Error:` line naming
  `claude plugin marketplace add shipd-now/shipd` is written to stderr and the
  exit code is `1`

#### Scenario: A failing marketplace refresh never reports up to date
- **WHEN** `claude plugin marketplace update shipd` exits nonzero
- **THEN** a single `Error:` line is written to stderr, no version comparison
  is reported, and the exit code is `1`

#### Scenario: An empty cache is an actionable error
- **WHEN** `shipd update` runs against a cache root holding no version
  directory
- **THEN** a single `Error:` line naming `claude plugin install s@shipd` is
  written to stderr and the exit code is `1`

#### Scenario: A failing apply is an error
- **WHEN** an update is available and `claude plugin update s@shipd` exits
  nonzero
- **THEN** a single `Error:` line is written to stderr and the exit code is `1`

#### Scenario: Update is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `update` among the verbs

## MODIFIED Requirements

### Requirement: Curated verb dispatch
id: cli-dispatch
base: da529672d8e2

The `shipd` binary SHALL expose exactly the curated verbs `init`, `list`,
`status`, `locate`, `related`, `epic`, `workspace`, `board`, `metrics`,
`lint`, `doctor`, `statusline`, `copilot`, `vendor`, `harness`, `install`,
and `update`, and for every verb except `list`, `doctor`, `statusline`,
`copilot`, `vendor`, `harness`, `install`, and `update` SHALL delegate by
replacing its own process with the mapped engine script invocation (`init` ->
`spec_status.py init`, `status` -> `spec_status.py show`, `locate`
-> `spec_status.py locate`, `related` -> `spec_status.py related`, `epic` ->
`spec_status.py epic-show`, `workspace` -> `spec_status.py workspace-show`,
`board` -> `dashboard.py` per the board-mode mapping below, `metrics` ->
`metrics.py`, `lint` -> `spec_lint.py`), passing all trailing arguments
through verbatim so the delegate's output and exit code are the binary's own.
When `metrics` is given no trailing arguments, the binary SHALL delegate to
`metrics.py summary`. When invoked as `shipd board`, the binary SHALL select
the delegate by the first trailing argument: the bare word `text` SHALL be
consumed and delegate to `dashboard.py board`, and any other first trailing
argument (or none) SHALL delegate to `dashboard.py tui` with all trailing
arguments intact. The binary SHALL resolve the engine scripts relative to its
own resolved file location. If the verb is unknown or missing — including the
retired `tui` — the binary SHALL print a usage banner listing the curated
verbs to stderr and exit `2`; when invoked with `help`, `-h`, or `--help` it
SHALL print the same banner to stdout and exit `0`.

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

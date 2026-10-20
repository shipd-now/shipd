# shipd-cli

### Requirement: Curated verb dispatch
id: cli-dispatch

The `shipd` binary SHALL expose exactly the curated verbs `init`, `list`,
`status`, `locate`, `related`, `search`, `prd`, `epic`, `workspace`,
`wiki`, `config`, `board`, `render`, `metrics`, `lint`, `worktree`, `room`,
`doctor`, `statusline`, `copilot`, `gate`, `vendor`, `harness`, `install`,
and `update`, and for every verb except `list`, `doctor`, `statusline`,
`copilot`, `gate`, `vendor`, `harness`, `install`, and `update` SHALL
delegate by
replacing its own process with the mapped script invocation (`init` ->
`spec_status.py init`, `status` -> `spec_status.py show`, `locate` ->
`spec_status.py locate`, `related` -> `spec_status.py related`, `search` ->
`spec_status.py search`, `prd` -> `spec_status.py prd-show`, `epic` ->
`spec_status.py epic-show`, `workspace` -> `spec_status.py` per the
workspace-mode mapping below, `wiki` -> `spec_status.py` per the wiki-mode
mapping below, `config` -> `spec_status.py config-show`, `board` ->
`dashboard.py` per the board-mode mapping below, `render` -> `render.py` per
the render-mode mapping below, `metrics` -> `metrics.py`, `lint` ->
`spec_lint.py`, `worktree` -> `worktree.py`, `room` -> `room.py`), passing
all trailing arguments through verbatim so the delegate's output and exit
code are the binary's own. Every delegate SHALL resolve under the engine's
`skills/build/scripts/` directory except `room.py`, which the binary SHALL
resolve under the room skill's own `skills/room/scripts/` directory through
a script-name-keyed override table, so the network-bearing room verbs never
enter the engine directory. When `metrics` is given no trailing arguments,
the binary SHALL delegate to `metrics.py summary`. When invoked as `shipd
workspace`, the binary SHALL select the delegate by the first trailing
argument: the bare word `init` SHALL be consumed and delegate to
`spec_status.py workspace-init`, the bare word `sync` SHALL be consumed and
delegate to `spec_status.py workspace-sync`, the bare word `team` SHALL be
consumed and delegate to `spec_status.py workspace-team`, and any other
first trailing argument (or none) SHALL delegate to `spec_status.py
workspace-show` with all trailing arguments intact. When invoked as `shipd
wiki`, the binary SHALL select the delegate by the first trailing argument:
the bare word `init` SHALL be consumed and delegate to `spec_status.py
wiki-init`, and any other first trailing argument (or none) SHALL delegate
to `spec_status.py wiki-show` with all trailing arguments intact. When
invoked as `shipd board`, the binary SHALL select the delegate by the first
trailing argument: the bare word `text` SHALL be consumed and delegate to
`dashboard.py board`, and any other first trailing argument (or none) SHALL
delegate to `dashboard.py tui` with all trailing arguments intact. When
invoked as `shipd render`, the binary SHALL select the delegate by the
first trailing argument: the bare word `output` SHALL be consumed and
delegate to `render.py output`, and any other first trailing argument (or
none) SHALL delegate to `render.py screen` with all trailing arguments
intact. The binary SHALL resolve the engine scripts relative to its own
resolved file location. If the verb is unknown or missing — including the
retired `tui` — the binary SHALL print a usage banner listing the curated
verbs to stderr and exit `2`; when invoked with `help`, `-h`, or `--help` it
SHALL print the same banner to stdout and exit `0`.

#### Scenario: Delegated verb preserves output and exit code
- **WHEN** `shipd locate no-such-change` runs in a repo where that change does
  not exist
- **THEN** the binary exits `1` with `Error: change 'no-such-change' not found`
  on stderr, exactly as `spec_status.py locate` does

#### Scenario: Room is a curated verb that delegates to the room skill
- **WHEN** `shipd room --help` runs
- **THEN** the banner of `shipd --help` lists `room` among the verbs, and the
  output is identical to `python3 plugins/s/skills/room/scripts/room.py
  --help` with exit code `0`, proving the delegate resolves under the room
  skill's scripts directory

#### Scenario: Room passes trailing arguments through
- **WHEN** `shipd room frobnicate` runs
- **THEN** `room.py`'s own usage error is printed — not the shipd banner — and
  the binary exits `2`

#### Scenario: Workspace init mode
- **WHEN** `shipd workspace init --help` runs
- **THEN** the output is identical to `spec_status.py workspace-init --help`
  and the exit code is `0`, proving the mode word is consumed and the
  remaining arguments pass through

#### Scenario: Workspace sync mode
- **WHEN** `shipd workspace sync --help` runs
- **THEN** the output is identical to `spec_status.py workspace-sync --help`
  and the exit code is `0`

#### Scenario: Workspace team mode
- **WHEN** `shipd workspace team --help` runs
- **THEN** the output is identical to `spec_status.py workspace-team --help`
  and the exit code is `0`

#### Scenario: Bare workspace is still the roster report
- **WHEN** `shipd workspace --help` runs
- **THEN** the output is identical to `spec_status.py workspace-show --help`
  and the exit code is `0`, proving non-mode arguments fall through intact

#### Scenario: Wiki init mode
- **WHEN** `shipd wiki init --help` runs
- **THEN** the output is identical to `spec_status.py wiki-init --help` and
  the exit code is `0`

#### Scenario: Bare wiki is the store report
- **WHEN** `shipd wiki --help` runs
- **THEN** the output is identical to `spec_status.py wiki-show --help` and
  the exit code is `0`

#### Scenario: Config delegates to the resolved-config report
- **WHEN** `shipd config` runs from a repo root
- **THEN** the output of `spec_status.py config-show` is printed — including
  its `config (resolved from …)` header line — and the exit code is `0`

#### Scenario: Wiki and config are curated verbs
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `wiki` and `config` among the verbs

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

#### Scenario: Bare render is the interactive viewer
- **WHEN** `shipd render --help` runs
- **THEN** the output is identical to `render.py screen --help` and the exit
  code is `0`, proving flags pass to the interactive delegate untouched

#### Scenario: Render output mode
- **WHEN** `shipd render output --plain <file>` runs on a markdown file
- **THEN** the output of `render.py output --plain <file>` is printed and the
  exit code is `0`

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

#### Scenario: Render is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `render` among the verbs

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

#### Scenario: Search is a curated verb that delegates
- **WHEN** `shipd search zzz-no-such-term` runs from a repo whose corpus
  contains no such term
- **THEN** the banner of `shipd --help` lists `search` among the verbs, and
  the invocation exits non-zero with the `Error:` line of
  `spec_status.py search`, proving the delegation

#### Scenario: Prd is a curated verb that delegates
- **WHEN** `shipd prd no-such-prd` runs from a workspace holding no such PRD
- **THEN** the banner of `shipd --help` lists `prd` among the verbs, and the
  invocation exits non-zero with the `Error:` line of
  `spec_status.py prd-show`, proving the delegation

#### Scenario: Gate is a curated in-binary verb
- **WHEN** `shipd --help` runs
- **THEN** the banner lists `gate`, and `shipd gate` is served by the binary
  itself rather than by replacing the process with a delegate

### Requirement: List in-flight changes
id: cli-list

When invoked as `shipd list [kind]`, the binary SHALL enumerate spec-library
artifacts of the given kind — `changes` (the default when the kind word is
omitted), `epics`, `verified`, `research`, `video`, or `docs` — obtaining the
rows from the engine's shared discovery seam (`spec_status.list_rows`), never
from a private re-walk of the tree, and printing one line per row with the
name, its location, and its status.

For `changes`, the binary SHALL probe the invocation root's
`<content-dir>/planned/` and, for each `.worktrees/<name>` directory that has
a `<content-dir>/planned/`, that worktree's planned changes, printing each
change's lifecycle status as read by the engine's status reader, deduping by
change name with the worktree occurrence winning. The binary SHALL exclude
completed changes unless `--all` is given, in which case entries from
`<content-dir>/completed/` are appended with status `archived`. If no
in-flight change exists, the binary SHALL print `no changes in flight` and
exit `0`.

For `epics`, the rows SHALL be the epics the engine's epic-discovery seam
yields — the invocation root's epics first, then epics hosted only under a
worktree, a contested slug appearing once with the invocation root winning —
each with the status read from its hosting root. For `verified`, `research`,
`video`, and `docs`, the rows SHALL be the slug directories of that kind under
each candidate root, deduped root-first, with no status value (rendered `-`
in text). If `--all` is combined with a kind other than `changes`, then the
binary SHALL exit non-zero with an error saying `--all` applies to changes
only.

Locations SHALL render `root` or `worktree:<name>`. At a workspace-level
invocation the listing SHALL additionally span each declared project universe
in slug order, a foreign universe's location prefixed with its project slug
(`<project>:<location>`). When `--root DIR` is passed explicitly, the listing
SHALL scope to that root's own universe (the root and its worktrees) and skip
workspace spanning. Invoked without an explicit `--root` from inside a member
repo, the listing resolves the single own universe, leaving the historical
output unchanged.

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

#### Scenario: Worktree-hosted epic is listed
- **WHEN** `shipd list epics --root <repo>` runs and only
  `<repo>/.worktrees/wt` hosts `epics/foo/epic.md` with `Status: active`
- **THEN** the output contains one line naming `foo`, `worktree:wt`, and
  `active`

#### Scenario: Contested epic slug is listed once, root winning
- **WHEN** an epic slug exists under both the root and a worktree and
  `shipd list epics --root <repo>` runs
- **THEN** exactly one line prints for it with location `root`

#### Scenario: Verified capabilities list without status
- **WHEN** `shipd list verified --root <repo>` runs on a repo with installed
  masters
- **THEN** one line prints per capability slug with location `root` and
  status `-`

#### Scenario: Installed documents list without status
- **WHEN** `shipd list docs --root <repo>` runs on a repo whose content
  directory holds `docs/payments-strategy/`
- **THEN** one line prints naming `payments-strategy` with location `root`
  and status `-`

#### Scenario: Empty docs listing prints its placeholder
- **WHEN** `shipd list docs --root <repo>` runs against a repo with no
  installed documents
- **THEN** the binary prints `no docs` and exits `0`

#### Scenario: --all refuses a non-changes kind
- **WHEN** `shipd list epics --all` runs
- **THEN** the binary exits non-zero with an error saying `--all` applies to
  changes only

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

The `shipd` binary SHALL provide a `doctor` verb that runs
environment preflight checks and prints one `ok <check> — <detail>`,
`warn <check> — <detail>`, or `fail <check> — <detail>` line per check
followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line, and
SHALL exit `1` if any check reports `fail` and `0` otherwise. The
required checks SHALL be: `python` (interpreter at least 3.9), `git`
(present on PATH), `config` (a resolvable layered configuration at the
working directory; a missing content directory is reported `ok` with a
note), and `pipeline` (the effective autonomous pipeline at the working
directory, resolved through the engine's resolver: `ok` naming the
resolved entry count and provenance when it resolves — the built-in
default included — and `fail` carrying the resolver's own error line
when a declared pipeline cannot resolve, whether from malformed entries,
or an unknown preset), with `pipeline` reported
directly after `config`. The warning checks SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `difft` (present on PATH, probed
via `shutil.which` so the binary stays stdlib-only, reported directly
after `gh`; the warning detail SHALL name the semantic review's
the semantic review being unable to run at all as the affected surface and
the tiered `semdiff doctor --fix` installer as the remedy, and a present
binary SHALL report `ok`), `textual` (importable, probed via
`importlib.util.find_spec` without importing it, so the binary itself
stays stdlib-only), `snapshot` (when the binary
runs from a plugin cache snapshot that is not the newest version
directory in the cache; when the binary runs from a repository checkout,
the check SHALL report dev mode as `ok`), and `statusline` (when the
Claude Code user settings file — default `~/.claude/settings.json` — is
absent, carries no `statusLine` key, or registers a command that does not
contain `integrations/statusline.sh`, probed read-only; the warning detail
SHALL name `shipd statusline install` as the remedy; for a registration
containing `integrations/statusline.sh`, the check SHALL run the binary's own
`integrations/statusline.sh --print-content-dir` with the working directory
as `current_dir`, and, when the engine's resolved content directory exists
and differs from the script's output, warn naming both directories; a
registration containing `integrations/statusline.sh` whose script resolves
the engine's content directory, or where that directory does not exist,
SHALL report `ok`). The `pip install` hint on the
`textual` detail SHALL name `-r requirements.txt` when a
`requirements.txt` exists at the working-directory root, and the pinned
package specifier (`'textual>=8.2.8,<9'`)
otherwise — a vendored per-repo install has no checkout to `-r` from.
Where the running interpreter is externally managed (PEP 668) — probed
read-only via the `EXTERNALLY-MANAGED` marker file in the interpreter's
stdlib directory resolved through `sysconfig` — the hint SHALL prepend
`--user --break-system-packages` to either form, so the printed command
is runnable by the interpreter that printed it; on an unmanaged
interpreter both hint forms SHALL remain unchanged. The verb SHALL report
no check for a package the engine does not depend on, so it SHALL report
no `pydantic` check and SHALL never escalate a dependency finding from a
declared `autonomous-pipeline`. The verb SHALL mutate nothing.

Bare `doctor` SHALL remain read-only: it SHALL install nothing, edit
nothing, and reach no network. Where `doctor` is invoked with `--fix`, it
SHALL additionally provision the environment autonomously, and SHALL state
the network access it performs before performing it. All mutation and all
network access SHALL occur only under `--fix`.

Under `--fix` the verb SHALL attempt every check that carries an automated
local remedy, in check order, and SHALL run each remedy without asking.
The automated remedies SHALL be the local-tooling ones only: the `textual`
package install the finding's own detail names, the review engine's tiered
`semdiff doctor --fix` installer for `difft`, and `shipd statusline
install` for an unregistered statusline. A check whose remedy mutates a
GitHub repository — `protection` and `automerge` — SHALL stay report-only
under `--fix`, naming the surface its absence affects and the
consent-gated skill that performs it, so an unattended run never alters a
shared repository's settings. A check with no automated remedy — `python`,
`config`, `pipeline`, an unauthenticated `gh`, and `copilot-secret` —
SHALL likewise report the surface its absence affects.

A remedy that fails SHALL NOT stop the run: the verb SHALL report the
failure with the surface it affects and continue to the remaining
remedies, so one unavailable installer never strands the rest of the
environment. After its own remedies, `--fix` SHALL delegate to the drive
CLI's `doctor --fix` as the final step, relaying its report, and SHALL
treat a missing drive CLI as one more reported finding rather than an
error. The verb SHALL then re-run every check and print the resulting
report, exiting on the re-run's own outcome rather than the first pass's.

#### Scenario: Healthy environment reports ok
- **WHEN** `shipd doctor` runs with python >= 3.9, git present, a resolvable
  config, a resolvable pipeline, gh authenticated, difft present, and the
  newest snapshot
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

#### Scenario: Missing difft only warns
- **WHEN** `shipd doctor` runs with no `difft` on PATH, all required checks
  passing
- **THEN** a `warn difft — ` line names that the semantic review cannot run
  and the `semdiff doctor --fix` remedy, and the exit code is `0`

#### Scenario: Present difft reports ok
- **WHEN** `shipd doctor` runs with `difft` on PATH
- **THEN** the `difft` check line begins `ok`

#### Scenario: Missing textual only warns
- **WHEN** `shipd doctor` runs without `textual` importable, all required
  checks passing
- **THEN** a `warn textual — ` line names the board as the only affected
  surface and the exit code is `0`

#### Scenario: No pydantic check is reported
- **WHEN** `shipd doctor` runs in any repo, with or without a declared
  `autonomous-pipeline` and with `pydantic` unimportable
- **THEN** no output line names `pydantic`, and neither the exit code nor
  the `pipeline` line's level depends on whether pydantic is importable

#### Scenario: Missing requirements.txt pins the hint
- **WHEN** `shipd doctor` runs without `textual` importable on an unmanaged
  interpreter in a repo whose root carries no `requirements.txt`
- **THEN** the `textual` detail's hint names `pip install
  'textual>=8.2.8,<9'` and never `-r requirements.txt`

#### Scenario: Externally managed interpreter flags the checkout hint
- **WHEN** `shipd doctor` runs without `textual` importable on an
  externally managed interpreter (the `EXTERNALLY-MANAGED` marker present)
  in a repo with a `requirements.txt` at its root
- **THEN** the `textual` detail's hint names
  `pip install --user --break-system-packages -r requirements.txt`

#### Scenario: Externally managed interpreter flags the pinned hint
- **WHEN** `shipd doctor` runs without `textual` importable on an externally
  managed interpreter in a repo whose root carries no `requirements.txt`
- **THEN** the `textual` detail's hint names
  `pip install --user --break-system-packages 'textual>=8.2.8,<9'`

#### Scenario: Stale snapshot warns
- **WHEN** `shipd doctor` runs from a cache snapshot directory that is not
  the newest version in the cache
- **THEN** a `warn snapshot — ` line names the newer version and the exit
  code is `0`

#### Scenario: Unregistered statusline only warns
- **WHEN** `shipd doctor` runs against a settings file with no `statusLine`
  key, all required checks passing
- **THEN** a `warn statusline — ` line names `shipd statusline install` as
  the remedy and the exit code is `0`

#### Scenario: Registered statusline reports ok
- **WHEN** `shipd doctor` runs against a settings file whose `statusLine`
  command contains `integrations/statusline.sh`
- **THEN** the `statusline` check line begins `ok`

#### Scenario: A foreign statusline warns
- **WHEN** `shipd doctor` runs against a settings file whose `statusLine`
  command does not contain `integrations/statusline.sh`
- **THEN** a `warn statusline — ` line names the registered command and
  `shipd statusline install` as the remedy

#### Scenario: Resolvable pipeline reports its provenance
- **WHEN** `shipd doctor` runs in a repo whose effective pipeline resolves
  (a declared list or preset, or no declaration at all)
- **THEN** an `ok pipeline — ` line names the resolved entry count and the
  provenance (`default` when no layer declares the key)

#### Scenario: Unresolvable declared pipeline fails the preflight
- **WHEN** `shipd doctor` runs in a repo declaring an `autonomous-pipeline`
  that cannot resolve — malformed entries or an unknown preset
- **THEN** a `fail pipeline — ` line carries the resolver's own error line
  and the exit code is `1`

#### Scenario: A declared pipeline resolves with no third-party package
- **WHEN** `shipd doctor` runs with `pydantic` unimportable in a repo
  declaring an `autonomous-pipeline` list, and again declaring the `eco`
  preset
- **THEN** the `pipeline` line is `ok` in both runs and the exit code is
  `0`

#### Scenario: Checkout run reports dev mode
- **WHEN** `doctor` runs from a repository checkout rather than a cache
  snapshot
- **THEN** the snapshot check reports `ok` and its detail names dev mode rather
  than comparing versions

#### Scenario: Bare doctor still installs nothing
- **WHEN** `shipd doctor` runs with a missing local tool
- **THEN** the tool is reported missing, no installation is attempted, and
  no network access occurs

#### Scenario: Fix installs a local tool without asking
- **WHEN** `shipd doctor --fix` runs with `difft` absent
- **THEN** the tiered `semdiff doctor --fix` installer runs with no consent
  prompt and the re-run reports `difft` present

#### Scenario: A GitHub mutation stays report-only under fix
- **WHEN** `shipd doctor --fix` runs in a repository whose default branch
  lacks the `semantic-review` context
- **THEN** no `gh api` call mutating the repository is made, and the
  `protection` finding names the surface it affects and the consent-gated
  skill that repairs it

#### Scenario: A failing remedy never strands the rest
- **WHEN** `shipd doctor --fix` runs with two automated remedies pending
  and the first one's installer exits non-zero
- **THEN** the failure is reported with the surface it affects, the second
  remedy still runs, and the verb completes

#### Scenario: Fix ends by delegating to the drive preflight
- **WHEN** `shipd doctor --fix` completes its own remedies
- **THEN** it invokes the drive CLI's `doctor --fix` as the final step and
  relays that report

#### Scenario: Fix exits on the state after repair
- **WHEN** `shipd doctor --fix` repairs every failing check
- **THEN** the printed report is the re-run's and the exit code is `0`

#### Scenario: A statusline that cannot see the engine's store warns
- **GIVEN** a registered shipd statusline and a working directory whose
  engine content directory exists but which the statusline script resolves
  differently
- **WHEN** `shipd doctor` runs
- **THEN** a `warn statusline — ` line names both directories

### Requirement: List JSON output
id: list-json

The `shipd list` verb SHALL accept a `--json` flag that emits the listing as
a JSON array on stdout — one object per row with `name`, `location`,
`status` (`null` for a kind without status values), and `project` (the owning
declared project's slug, `null` in the invocation root's own universe), in
the same order and with the same rows as the text mode, including the
archived rows under `--all` — and nothing else. An empty listing SHALL emit
an empty JSON array. Without the flag the text output SHALL stay
byte-identical for the `changes` kind in a non-workspace repo, and delegated
verbs SHALL keep passing `--json` through to their engine scripts verbatim.

#### Scenario: List rows are machine-readable
- **WHEN** `shipd list --json` runs in a repo with an in-flight change in a
  worktree
- **THEN** stdout parses as a JSON array whose entry carries the change
  name, its `worktree:<name>` location, its status, and `project` `null`

#### Scenario: Epic rows are machine-readable
- **WHEN** `shipd list epics --json` runs in a repo hosting one epic at the
  root
- **THEN** stdout parses as a JSON array whose entry carries the epic slug,
  location `root`, its status value, and `project` `null`

#### Scenario: Empty listing is an empty array
- **WHEN** `shipd list --json` runs with no changes in flight
- **THEN** stdout is an empty JSON array, not the text placeholder

#### Scenario: Delegated verbs pass the flag through
- **WHEN** `shipd epic <slug> --json` runs
- **THEN** the output is exactly `spec_status.py epic-show <slug> --json`'s
  output

### Requirement: Statusline registration verb
id: statusline-verb

The `shipd` binary SHALL provide a `statusline` verb over the Claude Code
user settings file, defaulting to `~/.claude/settings.json` and overridable
with `--settings <path>`. When invoked bare, the verb SHALL be read-only:
report whether the settings file registers a `statusLine` command, print the
registered command when one exists, and print the command this installation
would register. When invoked as `statusline install`, the verb SHALL write
the entry `"statusLine": {"type": "command", "command": <cmd>}` into the
settings file — creating the file and its parent directory when absent, and
preserving every other key on rewrite via an atomic same-directory
temp-file-and-rename. The registered command SHALL be: when the binary runs
from a repository checkout, `bash <plugin-root>/integrations/statusline.sh`
with the absolute resolved plugin root; when the binary runs from a plugin
cache snapshot, a shell command that at render time lists the snapshot's
parent directory, orders the version directories with `sort -V`, and runs
the newest snapshot's `integrations/statusline.sh`. A registered command is
shipd's when it contains the text `integrations/statusline.sh`. If the
settings file already carries a `statusLine` entry whose command is not
shipd's, then `install` SHALL register `<cmd> --then <existing>`, with the
existing command shell-quoted as one argument, so shipd's line renders first
and the existing statusline renders after it. It SHALL print `added
statusline above existing statusline` naming the existing command, and exit
`0`. With `--force`, `install` SHALL instead replace the entry with `<cmd>`
alone. If the entry is already shipd's, then `install` SHALL write `<cmd>`
followed by the `--then` argument the entry already carries, if any, so a
re-run never chains shipd beneath itself; a result identical to the existing
entry SHALL succeed idempotently with the file unchanged. If
the settings file exists but does not parse as JSON, then the verb SHALL
report an error and exit `1` without writing. On success `install` SHALL
print the registered command and note that it takes effect in the next
session.

#### Scenario: Install registers into fresh settings
- **WHEN** `shipd statusline install --settings <path>` runs and `<path>`
  does not exist
- **THEN** the file is created with a `statusLine` entry of type `command`
  and the exit code is `0`

#### Scenario: Other settings keys survive the write
- **WHEN** `install` runs against a settings file carrying unrelated keys
- **THEN** the rewritten file carries the same unrelated keys unchanged plus
  the `statusLine` entry

#### Scenario: A foreign statusline is chained beneath shipd's
- **WHEN** `install` runs against a settings file whose `statusLine.command`
  is `node /x/claude-statusline.mjs` and `--force` is absent
- **THEN** the entry becomes `<cmd> --then 'node /x/claude-statusline.mjs'`,
  the output carries `added statusline above existing statusline`, and the
  exit code is `0`; with `--force` the entry is `<cmd>` alone

#### Scenario: An older shipd registration is upgraded in place
- **WHEN** `install` runs against an entry `bash /old/integrations/statusline.sh
  --then 'echo theirs'`
- **THEN** the entry becomes `<cmd> --then 'echo theirs'`, carrying exactly
  one `integrations/statusline.sh`

#### Scenario: Identical registration is idempotent
- **WHEN** `install` runs twice with the same settings path
- **THEN** the second run succeeds with exit `0` and the file content is
  unchanged

#### Scenario: Checkout registers the repo script path
- **WHEN** the binary runs from a repository checkout and `install` runs
- **THEN** the registered command is `bash` followed by the absolute
  checkout path to `integrations/statusline.sh`

#### Scenario: Snapshot registration survives plugin updates
- **WHEN** the binary runs from a versioned cache snapshot and `install`
  runs
- **THEN** the registered command resolves the newest version directory
  under the snapshot's parent at render time via `sort -V`, not a pinned
  version path

#### Scenario: Bare verb mutates nothing
- **WHEN** `shipd statusline --settings <path>` runs without `install`
- **THEN** the report is printed and `<path>` is not created or modified

#### Scenario: Malformed settings are never overwritten
- **WHEN** `install` runs against a settings file that is not valid JSON
- **THEN** the verb exits `1` reporting the parse problem and the file is
  byte-identical afterwards

### Requirement: Copilot review-skill maintenance verb
id: copilot-verb

The `shipd` binary SHALL provide a `copilot` verb that maintains the shipd
Copilot code-review skill in a target repository rooted at `--root DIR`
(default: the working directory), managing, when invoked without `--room`, exactly four files:
`.github/skills/code-review/SKILL.md`,
`.github/skills/code-review/scripts/semdiff.py`,
`.github/workflows/copilot-code-review.yml`, and
`.github/workflows/copilot-review-gate.yml`. The SKILL.md and both workflow
contents SHALL come from the plugin's `integrations/copilot/` templates,
resolved relative to the binary's own location, with the `{version}`
placeholder in each template's ownership marker (`<!-- shipd-copilot
v{version} -->` in SKILL.md, `# shipd-copilot v{version}` in each workflow)
replaced by the plugin manifest version; the installed `semdiff.py` SHALL be
a byte-identical copy of the plugin's `skills/review/scripts/semdiff.py` and
carries no marker of its own. A marker-bearing managed file (the SKILL.md or
either workflow) that exists without its ownership marker SHALL be treated
as foreign; an existing `semdiff.py` SHALL be treated as owned exactly when
the adjacent SKILL.md is owned, and as foreign otherwise. When invoked bare,
the verb SHALL be read-only and exit `0`, printing one state per managed file (these four, and the room wake set under its own heading) — `installed` (marker at the plugin version and, for the skill, a
byte-identical `semdiff.py`), `stale` (an older marker version or a
differing `semdiff.py`), `foreign`, or `absent` — plus a note that automatic
review is enabled through a GitHub branch ruleset and that the Copilot
code-review surface exposes no repository-side model selection. When invoked
as `copilot add` without `--room`, the verb SHALL write all four files atomically
(same-directory temporary file and rename, parent directories created),
refreshing files it owns so a repeated `add` is idempotent and upgrades
stale installs; if any managed path is foreign, then `add` SHALL refuse with
exit `1` naming that file and write nothing, unless `--force` is given. When
invoked as `copilot remove` without `--room`, the verb SHALL delete the managed files it
owns, remove the `.github/skills/code-review` directory tree only when
emptied, and succeed at exit `0` when files are already absent; if a managed
path is foreign, then `remove` SHALL refuse with exit `1` naming that file
and delete nothing, unless `--force` is given. The verb SHALL never invoke
`gh`, touch the network, or modify anything outside the paths it manages.

#### Scenario: Bare report on an empty repository
- **WHEN** `shipd copilot --root <dir>` runs against a directory with no
  managed files
- **THEN** all four managed files report `absent`, nothing is created, and
  the exit code is `0`

#### Scenario: Add installs the four managed files
- **WHEN** `shipd copilot add --root <dir>` runs against an empty directory
- **THEN** the SKILL.md and both workflows land with their markers carrying
  the plugin manifest version, `semdiff.py` is byte-identical to the
  plugin's copy, and the exit code is `0`

#### Scenario: Repeated add refreshes a stale install
- **WHEN** `add` runs against a repo whose installed SKILL.md marker names an
  older version
- **THEN** the files are rewritten at the current version and the exit code
  is `0`

#### Scenario: Add refuses a foreign file without force
- **WHEN** `add` runs and `.github/workflows/copilot-review-gate.yml` exists
  without the ownership marker and `--force` is absent
- **THEN** the verb exits `1` naming that file and no managed file is
  written; with `--force` the file is replaced and the exit code is `0`

#### Scenario: Remove deletes only what it owns
- **WHEN** `shipd copilot remove --root <dir>` runs against a marked install
- **THEN** the four managed files are deleted, the emptied
  `.github/skills/code-review` tree is pruned, and the exit code is `0`

#### Scenario: Remove refuses a foreign file without force
- **WHEN** `remove` runs and the installed SKILL.md carries no ownership
  marker and `--force` is absent
- **THEN** the verb exits `1` naming that file and deletes nothing

#### Scenario: Report distinguishes stale from installed
- **WHEN** the installed `semdiff.py` differs from the plugin's copy and the
  bare verb runs
- **THEN** the skill's report line is `stale` and the exit code is `0`

### Requirement: Per-repo vendor verb
id: vendor-verb

The `shipd` binary SHALL provide a `vendor` verb that maintains a vendored
per-repo install of the plugin in a target repository rooted at `--root DIR`
(default: the working directory), managing exactly four surfaces, with the
content directory resolved through the engine's layered configuration
(default `.shipd`): the vendored plugin tree `<content-dir>/plugin/s/` — a
recursive byte-identical copy of the running plugin tree, tests included but
`__pycache__` bytecode caches excluded from both the copy and drift
detection, resolved relative to the binary's own location; a generated
`<content-dir>/plugin/.claude-plugin/marketplace.json` declaring marketplace
`shipd` with the single plugin `s` at source `./s`; merged keys in the target's
`.claude/settings.json` — `enabledPlugins."s@shipd": true` and
`extraKnownMarketplaces.shipd` as a directory source at the resolved
`<content-dir>/plugin` with `"autoUpdate": true`, plus a `statusLine`
registration of the vendored `integrations/statusline.sh` only when the file
carries no `statusLine` key; and the scaffold directories
`<content-dir>/verified/`, `<content-dir>/planned/`, and
`<content-dir>/completed/`, each holding a `.gitkeep`, created only where
missing. The vendored tree SHALL be treated as owned exactly when
`<content-dir>/plugin/s/.claude-plugin/plugin.json` parses as JSON with name
`s`, its `version` serving as the ownership marker, and as foreign when the
plugin directory exists otherwise. When invoked bare, the verb SHALL be
read-only and exit `0`, printing one state — `installed` (marker at the running
plugin version and every vendored file byte-identical with none extraneous),
`stale` (an older marker, drifted content, or extraneous files), `foreign`, or
`absent` — per managed surface. When invoked as `vendor add`, the verb SHALL
write files atomically (same-directory temporary file and rename, parent
directories created), rewriting the vendored tree to byte equality with the
running plugin — pruning extraneous files — so a repeated `add` is idempotent
and upgrades stale installs, and SHALL apply the settings merge declaratively
while never replacing an existing `statusLine` value; if the vendored plugin
directory is foreign, then `add` SHALL refuse with exit `1` naming it and
write nothing, unless `--force` is given. When invoked as `vendor remove`, the
verb SHALL delete the owned `<content-dir>/plugin/` tree, remove the two
managed settings keys, remove a `statusLine` registration only when its
command points into the vendored tree, and leave the scaffold directories and
all spec content untouched, exiting `0` when the vendored tree is already
absent; if the vendored plugin directory is foreign, then `remove` SHALL
refuse with exit `1` naming it and delete nothing, unless `--force` is given.
If the target's `.claude/settings.json` exists but does not parse as JSON,
then `add` and `remove` SHALL refuse with exit `1` before any write —
`--force` governs only a foreign plugin directory, never an unparseable
settings file. The verb SHALL never invoke `gh` or `claude`, touch the
network, or modify anything outside the managed surfaces.

#### Scenario: Bare report on an empty repository
- **WHEN** `shipd vendor --root <dir>` runs against a directory with no
  managed surfaces
- **THEN** every surface reports `absent`, nothing is created, and the exit
  code is `0`

#### Scenario: Add installs the vendored plugin and its wiring
- **WHEN** `shipd vendor add --root <dir>` runs against an empty repository
- **THEN** `<dir>/.shipd/plugin/s/` is byte-identical to the running plugin
  tree including its test suites, the marketplace manifest names `shipd` with
  plugin `s` at `./s`, `.claude/settings.json` carries the two managed keys
  pointing at `.shipd/plugin` plus a statusline registration, the three
  scaffold directories exist with `.gitkeep`, and the exit code is `0`

#### Scenario: Add honors a configured content directory
- **WHEN** `vendor add` runs against a repo whose configuration declares a
  custom content `dir`
- **THEN** the plugin lands under `<custom-dir>/plugin/` and the settings
  `extraKnownMarketplaces.shipd` path names `<custom-dir>/plugin`

#### Scenario: Repeated add refreshes a stale install
- **WHEN** `add` runs against a repo whose vendored marker names an older
  version and whose vendored tree carries an extraneous file
- **THEN** the tree is rewritten at the running version, the extraneous file
  is pruned, and the exit code is `0`

#### Scenario: Add preserves an existing statusline
- **WHEN** `add` runs against a repo whose `.claude/settings.json` already
  carries a `statusLine` key
- **THEN** that `statusLine` value is unchanged while the two managed keys
  are still merged

#### Scenario: Add refuses a foreign plugin directory without force
- **WHEN** `add` runs and `<content-dir>/plugin/s/` exists without a parseable
  plugin manifest naming `s` and `--force` is absent
- **THEN** the verb exits `1` naming the foreign directory and writes
  nothing; with `--force` the tree is replaced and the exit code is `0`

#### Scenario: Remove deletes only what it owns
- **WHEN** `shipd vendor remove --root <dir>` runs against an owned install
  whose `planned/` holds a change
- **THEN** the `<content-dir>/plugin/` tree and the two managed settings keys
  are gone, the scaffold directories and the planned change remain, and the
  exit code is `0`

#### Scenario: Remove of an absent install succeeds
- **WHEN** `vendor remove` runs against a repository with no vendored tree
- **THEN** the verb exits `0` and deletes nothing

### Requirement: Doctor validates the PR mode key
id: doctor-pr-mode-check

The doctor verb's existing `config` check SHALL additionally validate the
`pr-mode` key by resolving it through the engine's accessor
(shipd-config pr-mode-key). If the resolved configuration declares an
invalid `pr-mode` value, then the `config` check SHALL report `fail`
carrying the resolver's own error line — which names the key, the
offending value, the accepted values, and the supplying config file. A
valid or undeclared key SHALL leave the check's existing
content-directory reporting unchanged, and the doctor check list SHALL
NOT grow a new check name for this validation.

#### Scenario: Invalid pr-mode fails the config check
- **GIVEN** a repo whose `.shipd-config.json` declares `"pr-mode": "always"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `fail` and its detail names `pr-mode`,
  the accepted values, and the supplying config file

#### Scenario: Declared draft mode passes the config check
- **GIVEN** a repo whose config declares `"pr-mode": "draft"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports `ok` with its usual
  content-directory detail

#### Scenario: Undeclared key changes nothing
- **GIVEN** a repo declaring no `pr-mode`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports exactly what it reported before this
  validation existed

### Requirement: Doctor GitHub-side gate checks
id: doctor-github-checks

The `doctor` verb SHALL additionally report four GitHub-side checks —
`protection`, `automerge`, `copilot-secret`, and `fast-pass`, in that order
directly after `statusline` — probed read-only through the `gh` CLI, each behind an
injectable runner so the test suite never touches the network, and each
reporting `warn` at worst. If `gh` is absent or unauthenticated, or the
working directory resolves no GitHub repository (via
`gh repo view --json nameWithOwner`), or any probe fails for any other
reason (offline, an API error, a missing payload field), then the affected
check SHALL report `ok` with a note naming why it was skipped or could not be
verified — the preflight SHALL never fail, and never warn falsely, from an
unreachable or unreadable GitHub API. The verb SHALL resolve the repository
payload (`gh api repos/<nwo>`: default branch, `allow_auto_merge`,
`permissions.admin`) at most once and reuse it across the checks, and every
`warn` detail SHALL state when the token lacks admin permission, so the
consuming skill knows the fix is unavailable. The verb SHALL continue to
mutate nothing.

The `protection` check SHALL probe
`gh api repos/<nwo>/branches/<default>/protection` and, when that probe does
not already show `semantic-review` required, also the effective branch rules
`gh api repos/<nwo>/rules/branches/<default>` (which includes organisation
rulesets and needs no admin permission), and SHALL judge the union of the
required status contexts from both: when the union contains `semantic-review`
it SHALL report `ok` naming the source (classic protection or a ruleset);
when a ruleset protects the branch (the rules list is non-empty) or classic
protection does, and the union omits `semantic-review`, it SHALL `warn`
naming the missing context and, for a ruleset, saying so; only when neither
source protects the branch (classic 404 and an empty rules list) SHALL it
`warn` naming the unprotected default branch, and then only when the
single-branch payload does not report the branch `protected: true`. When the
classic probe is 403 or 404, the check SHALL consult the rules list before the
single-branch payload's `protected` boolean, and a rules-list probe that fails
SHALL leave the classic outcome standing, never a false alarm. If the classic
probe is 404, the rules list decides nothing, and the single-branch payload
reports `protected: true`, then the check SHALL report `ok` saying the branch
is protected with its details needing admin access and its required status
contexts not checked, and SHALL NOT say the branch is not protected; a payload
reporting `protected: false`, or one that cannot be read, SHALL leave the
unprotected warning standing.

The `automerge` check SHALL report `ok` when the repository payload's
`allow_auto_merge` is `true`; when it is `false` and the resolved `pr-mode`
is `draft` it SHALL report `ok` with a draft-mode note; when it is `false`
otherwise it SHALL `warn`; when the field is absent it SHALL report `ok`
with an unverifiable note.

Where `.github/workflows/copilot-review-gate.yml` exists at the
working-directory root, the `copilot-secret` check SHALL probe the
repository's Actions secrets: it SHALL report `ok` naming the CLI reviewer
mode when `COPILOT_GITHUB_TOKEN` is listed, SHALL `warn` naming the
fail-open poll fallback when the listing succeeds without it, and SHALL
report `ok` with an unverifiable note when the listing is denied. Where that
workflow file does not exist, the check SHALL report `ok` with a skipped
note.

The `fast-pass` check SHALL probe the repository Actions variable
`SHIPD_FAST_PASS` read-only through the same injectable runner: it SHALL report
`ok` naming unattended merging as enabled where the variable reads exactly
`true`, `ok` naming it off where the variable is absent or reads anything else,
and `ok` with an unverifiable note where the read is denied. The check SHALL
never `warn`: the fast-pass being off is the safe default and the fast-pass
being on is a consented setting, so neither state is a problem to report.

#### Scenario: No GitHub remote skips every GitHub-side check
- **WHEN** `shipd doctor` runs in a repository that resolves no GitHub
  repository through `gh repo view`
- **THEN** `protection`, `automerge`, `copilot-secret`, and `fast-pass` each
  report `ok` with a note naming why they were skipped, and the exit code is
  unaffected

#### Scenario: Unprotected default branch warns
- **WHEN** `shipd doctor` runs where the protection probe returns 404 for the
  default branch
- **THEN** a `warn protection — ` line names the unprotected default branch

#### Scenario: A ruleset-protected branch is not called unprotected
- **WHEN** `shipd doctor` runs where the classic protection probe returns 404
  and the effective branch rules list a `required_status_checks` rule whose
  contexts include `semantic-review`
- **THEN** the `protection` line begins `ok` and names the ruleset as the
  source

#### Scenario: A ruleset without the semantic-review context warns
- **WHEN** the classic probe returns 404 and the effective rules list is
  non-empty but requires no `semantic-review` context
- **THEN** a `warn protection — ` line names the missing context and the
  ruleset, and does not say the branch is unprotected

#### Scenario: Protection missing the semantic-review context warns
- **WHEN** `shipd doctor` runs where the protection probe returns required
  status contexts without `semantic-review`
- **THEN** a `warn protection — ` line names the missing `semantic-review`
  context

#### Scenario: Non-admin token falls back to the protected boolean
- **WHEN** `shipd doctor` runs where the protection probe returns 403 and the
  branches listing reports the default branch `protected: true`
- **THEN** the `protection` line begins `ok` and notes the required contexts
  could not be verified without admin

#### Scenario: A 404 on a protected branch is not called unprotected
- **WHEN** `shipd doctor` runs where the protection probe returns 404, the
  effective branch rules are empty, and the single-branch payload reports the
  default branch `protected: true`
- **THEN** the `protection` line begins `ok`, says the details need admin
  access, and does not say the branch is not protected

#### Scenario: A 404 on an unprotected branch still warns
- **WHEN** `shipd doctor` runs where the protection probe returns 404, the
  effective branch rules are empty, and the single-branch payload reports the
  default branch `protected: false`
- **THEN** a `warn protection — ` line names the unprotected default branch

#### Scenario: Draft pr-mode waives the automerge warning
- **WHEN** `shipd doctor` runs where `allow_auto_merge` is `false` and the
  layered configuration declares `pr-mode: draft`
- **THEN** the `automerge` line begins `ok` and names the draft mode

#### Scenario: Disabled auto-merge warns under auto pr-mode
- **WHEN** `shipd doctor` runs where `allow_auto_merge` is `false` and no
  layer declares a `pr-mode`
- **THEN** a `warn automerge — ` line is printed and the exit code is `0`

#### Scenario: Installed gate without the secret warns fail-open
- **WHEN** `shipd doctor` runs where
  `.github/workflows/copilot-review-gate.yml` exists and the secrets listing
  succeeds without `COPILOT_GITHUB_TOKEN`
- **THEN** a `warn copilot-secret — ` line names the fail-open poll fallback

#### Scenario: Absent gate workflow skips the secret check
- **WHEN** `shipd doctor` runs in a repository with no
  `.github/workflows/copilot-review-gate.yml`
- **THEN** the `copilot-secret` line begins `ok` and notes the check was
  skipped

#### Scenario: An enabled fast-pass is reported
- **WHEN** `shipd doctor` runs where `SHIPD_FAST_PASS` reads `true`
- **THEN** the `fast-pass` line begins `ok` and names unattended merging as
  enabled

#### Scenario: An absent variable reports the fast-pass off
- **WHEN** `shipd doctor` runs where `SHIPD_FAST_PASS` is unset
- **THEN** the `fast-pass` line begins `ok` and names the fast-pass as off

#### Scenario: A denied variable read never warns
- **WHEN** `shipd doctor` runs where the variable read is denied
- **THEN** the `fast-pass` line begins `ok` with an unverifiable note and the
  exit code is `0`

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

### Requirement: Doctor schema check
id: doctor-schema-check

The doctor preflight SHALL include a `schema` check reporting the repo's
schema version against the engine's `SCHEMA_VERSION`: `ok` naming the
version (and whether it was read from the marker or assumed) when the
majors match and the repo's minor is not ahead, `warn` when the repo's
minor is ahead of the engine's, and `fail` naming both versions and the
remedy on a major mismatch. The check SHALL report rather than raise, so a
mismatched repo still completes its preflight.

#### Scenario: Healthy repo reports ok
- **GIVEN** a repo whose marker equals the engine's version
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `ok schema` naming the version

#### Scenario: Major mismatch is a fail line, not a crash
- **GIVEN** a repo whose marker carries a different major
- **WHEN** `shipd doctor` runs
- **THEN** the output carries `fail schema` naming both versions and the
  preflight still completes its remaining checks

### Requirement: Doctor wiki-store check
id: doctor-wiki-check

The `doctor` verb SHALL include a report-only `wiki` check, printed directly
after the `schema` check, naming the wiki store the working directory
resolves: when a workspace chain exists, the detail SHALL name the nearest
member's store path and whether it is present or absent; when no workspace is
discoverable but the resolved content directory exists, the detail SHALL name
the repo-local fallback store path, whether it is present or absent, and that
`wiki-init` scaffolds an absent one; when neither exists, the detail SHALL
state that no store is resolvable, naming the missing workspace and content
directory. The check SHALL always report `ok` — it informs which store
resolved and never gates the preflight — and SHALL mutate nothing.

#### Scenario: Bare repo reports the fallback store
- **WHEN** `shipd doctor` runs in a repo with a content directory and no
  workspace
- **THEN** the output carries an `ok wiki — …` line naming
  `<root>/<content-dir>/wiki` as the repo-local fallback store

#### Scenario: Workspace repo reports the chain store
- **WHEN** `shipd doctor` runs in a repo under a workspace
- **THEN** the `ok wiki — …` line names the nearest workspace member's store
  path

#### Scenario: The check never fails the preflight
- **WHEN** `shipd doctor` runs where no store is resolvable at all
- **THEN** the `wiki` line still reports `ok`, naming what is missing, and
  the check contributes nothing to the exit code

### Requirement: Doctor validates the workspaces root key
id: doctor-workspaces-root-check

The doctor verb's existing `config` check SHALL additionally validate the
`workspaces_root` key by resolving it through the engine's accessor
(shipd-config workspaces-root-key). If the resolved configuration declares a
malformed `workspaces_root` value, then the `config` check SHALL report
`fail` carrying the accessor's own error line, which names the key. If the
resolved value is well-formed but the declared root is not an existing
directory, then the `config` check SHALL report `warn` naming
`workspaces_root` and the missing path — report-only, mutating nothing. A
valid-and-present or undeclared key SHALL leave the check's existing
reporting unchanged, and the doctor check list SHALL NOT grow a new check
name for this validation.

#### Scenario: Malformed value fails the config check
- **GIVEN** a repo whose `.shipd-config.json` declares
  `"workspaces_root": "relative/path"`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `fail` and its detail names
  `workspaces_root`

#### Scenario: Missing declared root warns
- **GIVEN** a config declaring `workspaces_root` naming a directory that does
  not exist
- **WHEN** `shipd doctor` runs
- **THEN** the `config` line begins `warn` naming `workspaces_root` and the
  missing path, and the exit code reflects no failure from this check

#### Scenario: Declared existing root passes unchanged
- **GIVEN** a config declaring `workspaces_root` naming an existing directory
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check reports `ok` with its usual content-directory
  detail

#### Scenario: Undeclared key changes nothing
- **GIVEN** a repo whose layers declare no `workspaces_root`
- **WHEN** `shipd doctor` runs
- **THEN** the `config` check's reporting is identical to the pre-existing
  behavior

### Requirement: Doctor external-store check
id: doctor-store-check

The `doctor` preflight SHALL report a `store` check line naming the external
store the working directory resolves, positioned directly after the `wiki` line
in the check roster. Where the resolved configuration declares no `store_root`,
the check SHALL report `ok` stating that the content directory is in-repo.
Where `store_root` is declared, the check SHALL report `ok` naming the resolved
absolute content directory. If a directory exists at the store root joined with
the basename fallback path, that path differs from the resolved content
directory, and it still holds any of the `verified/`, `planned/`, `completed/`,
or `research/` content-layout subdirectories, then the check SHALL report
`warn` naming both paths and a `git mv` remedy. The warning SHALL be keyed on
the flat folder still holding content rather than on the resolved directory
being absent, so it survives the first engine write to the resolved location.
The
check SHALL mutate nothing and SHALL never move, create, or delete a store
directory. If the configuration is malformed, then the check SHALL report `ok`
carrying the error as its detail, leaving the `config` check to own config
failures.

#### Scenario: No store declared reports in-repo
- **GIVEN** a repository whose resolved configuration declares no `store_root`
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` and states the content directory is
  in-repo

#### Scenario: Resolved store is named
- **GIVEN** a repository resolving an external store that exists
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` naming the resolved absolute content
  directory

#### Scenario: Stranded flat folder warns with both paths
- **GIVEN** a declared registry member whose store root holds a `verified/`
  directory under the basename fallback path while the registry-path directory
  is absent
- **WHEN** the preflight runs
- **THEN** the `store` line reports `warn`, names the existing basename path and
  the resolved registry path, and names a `git mv` remedy

#### Scenario: The warning survives the first write to the resolved location
- **GIVEN** that same stranded basename path still holding its `verified/`
  directory, and the registry-path directory now present
- **WHEN** the preflight runs
- **THEN** the `store` line still reports `warn` naming the stranded basename
  path, rather than reporting `ok`

#### Scenario: The check moves nothing
- **WHEN** the preflight runs against a stranded flat folder
- **THEN** no directory is created, moved, or deleted, and the preflight's exit
  code is unchanged by the warning

#### Scenario: Malformed config is reported, not double-failed
- **GIVEN** a repository whose configuration fails to resolve
- **WHEN** the preflight runs
- **THEN** the `store` line reports `ok` carrying the error as its detail

### Requirement: Doctor store-sync check
id: doctor-store-sync-check

The `doctor` verb SHALL report a `store-sync` check naming how far the
resolved store's checkout has drifted from its upstream. The check SHALL
probe with local git only — the upstream's configured name and the
ahead/behind counts from `git rev-list --count --left-right @{u}...HEAD` —
and SHALL never fetch, push, or otherwise reach the network, and SHALL mutate
nothing. Where the store resolves to a workspace or external store inside a
git work tree whose branch has an upstream, the check SHALL report `warn`
naming the unpushed and unpulled commit counts and the store path when either
count is non-zero, and `ok` when both are zero. Where no store resolves, the
store is not inside a git work tree, the branch has no upstream, or the store
is the repo-local fallback, the check SHALL report `ok` naming why no
comparison applies. A malformed configuration SHALL be reported as the detail
rather than failing the preflight, so the check never double-fails what the
`config` check owns.

#### Scenario: Unpushed commits warn with their count
- **GIVEN** a workspace store whose branch is 12 commits ahead of its
  upstream and 0 behind
- **WHEN** `shipd doctor` runs
- **THEN** a `warn store-sync — …` line names 12 unpushed commits and the
  store path, and the preflight's exit code is 0

#### Scenario: A synced store reports ok
- **GIVEN** a workspace store whose branch matches its upstream exactly
- **WHEN** `shipd doctor` runs
- **THEN** an `ok store-sync — …` line is printed

#### Scenario: No upstream reports ok
- **GIVEN** a workspace store whose current branch has no upstream configured
- **WHEN** `shipd doctor` runs
- **THEN** an `ok store-sync — …` line names that no comparison applies

#### Scenario: The check never reaches the network
- **WHEN** `shipd doctor` runs against a store whose remote is unreachable
- **THEN** the `store-sync` line is printed without any fetch being attempted

### Requirement: Doctor local-state check
id: doctor-local-state-check

The `doctor` verb SHALL additionally report a `local-state` check, directly
after `store-sync` and before `gh`, covering the two local-state paths the engine writes but
never commits: `<content-dir>/state.json` and `<content-dir>/autopilot/`.
The check SHALL report `warn` when either path is tracked by git at the
working directory, naming the tracked paths, and `warn` when the root's
`.gitignore` lacks either rule, naming the missing rules; either detail SHALL
name `shipd init` as the remedy. When both rules are present and neither path
is tracked, the check SHALL report `ok` naming the rules. If the content
directory resolves outside the repository, or the working directory is not a
git checkout, then the check SHALL report `ok` with a note naming why it was
skipped. The check SHALL be report-only: it SHALL mutate nothing, and under
`--fix` it SHALL stay report-only, naming the surface its finding affects
and `shipd init` as the manual remedy, so the automated remedy set is
unchanged.

#### Scenario: Tracked state file warns
- **GIVEN** a git checkout whose committed tree tracks `.shipd/state.json`
- **WHEN** `shipd doctor` runs
- **THEN** a `warn local-state — ` line names `.shipd/state.json` and
  `shipd init`, and the exit code is `0`

#### Scenario: Missing ignore rule warns
- **GIVEN** a git checkout tracking neither path whose `.gitignore` lacks
  `.shipd/autopilot/`
- **WHEN** `shipd doctor` runs
- **THEN** a `warn local-state — ` line names the missing rule and
  `shipd init`

#### Scenario: Ignored and untracked reports ok
- **GIVEN** a git checkout whose `.gitignore` carries both rules and tracks
  neither path
- **WHEN** `shipd doctor` runs
- **THEN** the `local-state` line begins `ok`

#### Scenario: Not a checkout is skipped
- **WHEN** `shipd doctor` runs in a directory with no `.git` entry
- **THEN** the `local-state` line begins `ok` and its detail says the check
  was skipped

#### Scenario: Check order follows store-sync
- **WHEN** `shipd doctor` runs
- **THEN** the `local-state` line is printed directly after the `store-sync` line and before the `gh` line

#### Scenario: Stays report-only under fix
- **WHEN** `shipd doctor --fix` runs with `local-state` warning
- **THEN** no remedy runs for it, and the report-only line names `shipd init`

### Requirement: Copilot room wake set
id: copilot-room-wake

Where `--room` is given, the `copilot` verb SHALL act only on the room wake
set: `.github/workflows/room-wake.yml`, rendered from the plugin's
`integrations/copilot/room-wake.yml` with `{version}` replaced in its
`# shipd-copilot v{version}` marker, and five runtime files under
`.github/shipd-room/` byte-identical to the plugin's
`.claude-plugin/plugin.json`, `skills/room/scripts/room.py`,
`skills/room/scripts/room_schema.py`, `skills/build/scripts/spec_common.py`
and `skills/build/scripts/cli_common.py`, at those same relative paths. A
runtime file SHALL be owned exactly when the wake workflow carries its
marker and `stale` when its bytes differ from the plugin's, and the workflow
SHALL report `stale` while any runtime file is not `installed`. `add
--room` SHALL prepare every payload before the first write and write the six
files atomically; `remove --room` SHALL delete the owned files and prune the
emptied `.github/shipd-room/` directories innermost first; if a wake path is
foreign, then both SHALL refuse with exit `1` naming it unless `--force` is
given. Without `--room`, `add` and `remove` SHALL leave the wake set
untouched.

#### Scenario: Add room installs the wake set only
- **WHEN** `shipd copilot add --room --root <dir>` runs on an empty
  directory
- **THEN** `room-wake.yml` carries the manifest version marker, the five
  runtime files are byte-identical to the plugin's, none of the four gate
  files exists, and the exit code is `0`

#### Scenario: Plain add leaves the wake set alone
- **WHEN** plain `shipd copilot add` runs on a directory holding a stale
  wake set
- **THEN** the wake files are byte-unchanged and the four gate files are
  written

#### Scenario: Drifted runtime is stale
- **WHEN** an installed `.github/shipd-room/skills/room/scripts/room.py`
  differs from the plugin's and the bare verb runs
- **THEN** that file and `room-wake.yml` both report `stale`, and the exit
  code is `0`

#### Scenario: Foreign wake workflow refuses without force
- **WHEN** `add --room` runs and `room-wake.yml` exists without the marker
- **THEN** the verb exits `1` naming it and writes nothing; with `--force`
  it writes all six files

#### Scenario: Remove room prunes the runtime tree
- **WHEN** `remove --room` runs on an installed wake set beside an installed
  gate
- **THEN** the six wake files and the emptied `.github/shipd-room` tree are
  gone, the four gate files remain, and the exit code is `0`

### Requirement: Statusline layout setting
id: statusline-layout

The user-level `~/.shipd-config.json` SHALL carry the statusline layout under
the key `statusline` as `{"lines": [[<seg>, ...], ...]}`, where each inner
list is one output line and each `<seg>` is one of `spec`, `directory`, or
`context`. When the key is absent the layout SHALL be `[["spec",
"context"]]`. `shipd statusline install` SHALL render the layout into the
registered command as one `--line <seg>,<seg>` argument per line, placed
before any `--then` argument. The `install` verb SHALL accept repeatable
`--show <seg>` (append the segment to the end of the first line when the
layout lacks it) and `--hide <seg>` (remove it from every line, dropping a
line left empty), and SHALL save the resulting layout to
`~/.shipd-config.json` before registering, preserving every other key. A
`shipd statusline layout` verb SHALL print the saved layout one line per
output line when bare, and when given one or more `<seg>,<seg>` arguments
SHALL save them as the layout, one argument per line, and re-register the
statusline when shipd's statusline is registered. A segment name outside the
three, a segment named twice, or a layout with no segment SHALL be refused
with exit `2` naming the problem, writing nothing. A malformed `statusline`
value in the config file SHALL make both verbs exit `1` naming the key,
writing nothing.

#### Scenario: Install renders the default layout
- **WHEN** `shipd statusline install` runs with no `statusline` key saved
- **THEN** the registered command carries `--line spec,context`

#### Scenario: Show appends and persists
- **WHEN** `shipd statusline install --show directory` runs with no saved
  layout
- **THEN** `~/.shipd-config.json` holds
  `{"lines": [["spec", "context", "directory"]]}` and the registered command
  carries `--line spec,context,directory`

#### Scenario: Layout verb sets two lines
- **WHEN** `shipd statusline layout spec,context directory` runs with
  shipd's statusline registered
- **THEN** the config holds `[["spec", "context"], ["directory"]]` and the
  registered command carries `--line spec,context --line directory`, keeping
  any `--then` argument

#### Scenario: Context first is saved in order
- **WHEN** `shipd statusline layout context,spec` runs
- **THEN** the config holds `[["context", "spec"]]`

#### Scenario: An unknown segment is refused
- **WHEN** `shipd statusline layout spec,clock` runs
- **THEN** the exit code is `2`, the message names `clock`, and neither file
  changes

### Requirement: Gate rules verb
id: gate-rules-verb

The `shipd gate rules` verb SHALL be served by the binary through a stdlib-only
engine module `merge_rules.py` beside `spec_common.py`, and every GitHub call
SHALL go through one injectable runner `run(args, stdin=None, cwd=None)`
returning `(returncode, stdout, stderr)`. The repository is `--repo
OWNER/NAME` when given, else the one `gh repo view` resolves from `--root`
(default the cwd). Bare `shipd gate rules` SHALL print the resolved `merge`
configuration beside the live ruleset named `shipd merge rules`, one line per
member with an `ok` or `differs` mark, write nothing, and exit `0` even when
they differ. `shipd gate rules apply` SHALL create that ruleset (POST) when no
repository-sourced ruleset carries the name, update it in place (PUT by id)
when exactly one does, and print one line per changed member as `member: live
-> wanted`; when nothing differs it SHALL write nothing and say so. The
ruleset body SHALL be: target `branch`, enforcement `active`, conditions
`ref_name` including `~DEFAULT_BRANCH`, empty `bypass_actors`, a
`pull_request` rule carrying `required_approving_review_count` from
`approvals`, `dismiss_stale_reviews_on_push` from `dismiss_stale`,
`require_last_push_approval` from `last_push_approval`,
`required_review_thread_resolution` from `thread_resolution`, and
`require_code_owner_review` false with no `allowed_merge_methods`; and a
`required_status_checks` rule listing each `required_checks` context with
`strict_required_status_checks_policy` from `strict` (the rule is omitted when
the list is empty). The verb SHALL never write to, or read the detail of, any
ruleset other than the one it owns, SHALL fail with `Error:` and exit `1` on a
`ConfigError`, a duplicate-named ruleset, or a failed GitHub call (a 403
naming the missing admin permission), and SHALL be reported by `shipd --help`.

#### Scenario: Apply creates the ruleset when absent
- **WHEN** `shipd gate rules apply` runs against a fake runner whose ruleset
  list is empty
- **THEN** exactly one POST to `repos/<nwo>/rulesets` is made whose body
  carries the default merge rules, and each member prints as created

#### Scenario: Apply updates only the owned ruleset
- **WHEN** the list holds `main` and `shipd merge rules` and the latter's
  approvals differ from config
- **THEN** one PUT goes to the owned ruleset's id, nothing is written to
  `main`, and the output shows `approvals: 0 -> 2`

#### Scenario: Apply with no drift writes nothing
- **WHEN** the live ruleset already matches the configuration
- **THEN** no POST or PUT is made and the output says nothing was written

#### Scenario: Bare verb reports and changes nothing
- **WHEN** `shipd gate rules` runs with a live ruleset that differs
- **THEN** the output marks the differing members `differs`, no write call is
  made, and the exit code is `0`

#### Scenario: Duplicate name is refused
- **WHEN** two repository rulesets are named `shipd merge rules`
- **THEN** apply writes nothing and exits `1` naming the duplicate

### Requirement: Doctor merge-rules drift check
id: doctor-merge-rules-check

The `doctor` verb SHALL report a `merge-rules` check directly after
`fast-pass`, read-only through the injectable `gh` runner. It SHALL resolve the
`merge` configuration with `resolve_merge`, find the repository's
`shipd merge rules` ruleset with `merge_rules.find_owned`, and compare them
with `merge_rules.diff` (all from `merge-rules-config`). When nothing differs
it SHALL report `ok`. When members differ, or no such ruleset exists, it SHALL
`warn` with one line listing each differing member as `member: live X, wanted
Y` joined by `; `, ending with a pointer to `shipd gate rules` (the
member-per-line report) and `shipd gate rules apply` through `/s:gate`. When the
`merge` configuration is invalid it SHALL `warn` naming the error. When GitHub
is unreadable, the ruleset lookup raises, or the context is skipped, it SHALL
report `ok` with a skipped or unverifiable note. The check SHALL write nothing.

#### Scenario: Matching ruleset is ok
- **WHEN** the live `shipd merge rules` ruleset matches the resolved config
- **THEN** the `merge-rules` line begins `ok`

#### Scenario: Drift is warned member by member
- **WHEN** the live ruleset requires 0 approvals and config wants 2
- **THEN** a `warn merge-rules — ` line contains `approvals: live 0, wanted 2`
  and names `shipd gate rules`, and the exit code is `0`

#### Scenario: Missing ruleset warns
- **WHEN** no ruleset named `shipd merge rules` exists
- **THEN** a `warn merge-rules — ` line names `shipd gate rules apply`

#### Scenario: Unreadable GitHub never warns
- **WHEN** the ruleset lookup fails or raises
- **THEN** the line begins `ok` with a note that it could not be verified

### Requirement: Doctor Actions-approval check
id: doctor-actions-approve-check

The `doctor` verb SHALL report an `actions-approve` check directly after
`merge-rules`. Where `.github/workflows/copilot-review-gate.yml` exists at the
root it SHALL read `gh api repos/<nwo>/actions/permissions/workflow` and report
`ok` when `can_approve_pull_request_reviews` is `true`, and `warn` when it is
`false`, saying the CI reviewer cannot approve until an admin enables the
setting through `/s:gate`. Where the workflow is absent, the context is
skipped, or the read is denied, it SHALL report `ok` with a skipped or
unverifiable note. The check SHALL write nothing.

#### Scenario: Setting off warns where the gate is installed
- **WHEN** the gate workflow exists and the setting reads `false`
- **THEN** a `warn actions-approve — ` line is printed

#### Scenario: Setting on is ok
- **WHEN** the gate workflow exists and the setting reads `true`
- **THEN** the line begins `ok`

#### Scenario: No gate workflow skips
- **WHEN** the gate workflow is absent
- **THEN** the line begins `ok` and notes it was skipped

### Requirement: New GitHub checks are report-only under fix
id: doctor-new-checks-report-only

Under `doctor --fix` the `merge-rules` and `actions-approve` checks SHALL stay
report-only, naming `/s:gate` (`shipd gate rules apply`) as the consent-gated
remedy, and a `protection` finding sourced from a ruleset SHALL likewise run no
remedy.

#### Scenario: Fix performs no GitHub mutation for the new checks
- **WHEN** `shipd doctor --fix` meets a `warn merge-rules` line
- **THEN** no `gh` mutation runs and the line carries a `/s:gate` fix hint

### Requirement: Copilot update refreshes every installed set
id: copilot-update

When invoked as `copilot update`, the `copilot` verb SHALL refresh the four gate files exactly as `copilot add` does, and SHALL also refresh the room wake set where its "room-wake.yml" carries the shipd-copilot ownership marker (reported `installed` or `stale`). Where the wake workflow is absent or carries no marker, the verb SHALL leave every wake path untouched and print one line saying the wake set was left as is, without changing the exit code. The verb SHALL prepare every payload it will write before the first write. If any of the four gate files is foreign, then `update` SHALL refuse with exit `1` naming it and write nothing, unless `--force` is given; `--force` SHALL NOT cause a wake path to be written. If `--room` is given with `update`, then the verb SHALL exit `2` with a usage error and write nothing. `copilot add`, with or without `--room`, SHALL keep its behaviour unchanged.

#### Scenario: Update refreshes an installed stale wake set
- **WHEN** `shipd copilot update --root <dir>` runs on a directory holding a stale gate install and a wake set whose workflow marker names an older version and whose bundled room runtime has drifted
- **THEN** the four gate files and all six wake files are written at the running version, the bare report shows all ten `installed`, and the exit code is `0`

#### Scenario: Update never installs the wake set fresh
- **WHEN** `update` runs on a directory with a gate install and no wake files
- **THEN** the four gate files are written, no wake path exists afterwards, the output says the wake set was left as is, and the exit code is `0`

#### Scenario: A foreign wake workflow is skipped, not refused
- **WHEN** `update` runs and "room-wake.yml" exists without the marker
- **THEN** the gate files are written, the wake workflow is byte-unchanged, and the exit code is `0`

#### Scenario: A foreign gate file refuses the whole update
- **WHEN** `update` runs on a directory holding a stale wake set and a foreign gate workflow
- **THEN** the verb exits `1` naming the gate workflow and every file is byte-unchanged

#### Scenario: Room flag is a usage error
- **WHEN** `shipd copilot update --room` runs
- **THEN** the exit code is `2` and nothing is written

### Requirement: Copilot report points stale files at update
id: copilot-report-update-hint

Where the bare `copilot` verb reports a managed gate file or a room wake file as `stale`, the line's detail SHALL name `shipd copilot update` as the refresh, and SHALL NOT name `shipd copilot add` or `shipd copilot add --room` as the refresh. The stale states themselves, the other states' details, and the report's closing lines SHALL stay unchanged.

#### Scenario: A stale gate file names update
- **WHEN** the bare report runs on a gate install whose workflow marker names `v0.0.1`
- **THEN** the workflow's line is `stale`, contains `0.0.1` and `shipd copilot update`, and contains no "copilot add` refreshes"

#### Scenario: A stale wake set names update
- **WHEN** the bare report runs on a wake set whose bundled `room.py` has drifted
- **THEN** each stale wake line names `shipd copilot update` and none contains `add --room`

#### Scenario: Copilot suite passes
- **WHEN** `python3 -m unittest discover -s plugins/s/skills/build/tests -p test_copilot_verb.py` runs
- **THEN** it reports `OK`

### Requirement: Room wake bundle is self-contained
id: copilot-room-wake-self-contained

The five runtime files that `shipd copilot add --room` installs under
`.github/shipd-room/` SHALL be self-contained for every `room.py` verb except
`run`: where the installed `room.py` runs under `python3 -I -B`, each of
`join`, `list`, `whoami`, `message`, `close` and `watch` SHALL parse
`--help` with exit `0` and no traceback. The bundled `run` SHALL fail per
room-runner `room-run-missing-modules`, so the bundle list stays the five
files named in `copilot-room-wake`. `docs/room-wake-reference.md` SHALL state
that the bundle omits `run` and point at `shipd room run`, and SHALL lint
clean. `plugin.json` SHALL carry a version one patch above `main`'s.

#### Scenario: Every wake verb loads from the installed bundle
- **WHEN** `shipd copilot add --room --root <dir>` has run and
  `python3 -I -B <dir>/.github/shipd-room/skills/room/scripts/room.py <verb> --help`
  runs for each of `join`, `list`, `whoami`, `message`, `close`, `watch`
- **THEN** each exits `0` and its stderr holds no `Traceback`

#### Scenario: The bundled run fails with one Error line
- **WHEN** the installed bundle's `room.py run 1 --role reviewer` runs
- **THEN** stderr holds exactly one line, it starts with `Error:` and names
  `shipd room run`, stderr holds no `Traceback`, and the exit code is `1`

#### Scenario: The wake reference names the omission
- **WHEN** `docs_lint.py docs/room-wake-reference.md` runs
- **THEN** it exits `0`, and the file names `shipd room run` beside the
  bundled `room.py` row

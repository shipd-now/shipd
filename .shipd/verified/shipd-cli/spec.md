# shipd-cli

### Requirement: Curated verb dispatch
id: cli-dispatch

The `shipd` binary SHALL expose exactly the curated verbs `list`, `status`,
`locate`, `epic`, `workspace`, `board`, `metrics`, `lint`, `doctor`,
`statusline`, `copilot`, and `vendor`, and for every verb except `list`,
`doctor`, `statusline`, `copilot`, and `vendor` SHALL delegate by replacing
its own process with the mapped engine script invocation (`status` ->
`spec_status.py show`, `locate` -> `spec_status.py locate`, `epic` ->
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
SHALL exit `1` if any check reports `fail` and `0` otherwise. The
required checks SHALL be: `python` (interpreter at least 3.9), `git`
(present on PATH), `config` (a resolvable layered configuration at the
working directory; a missing content directory is reported `ok` with a
note), and `pipeline` (the effective autonomous pipeline at the working
directory, resolved through the engine's resolver: `ok` naming the
resolved entry count and provenance when it resolves — the built-in
default included — and `fail` carrying the resolver's own error line
when a declared pipeline cannot resolve, whether from malformed entries,
an unknown preset, or missing pydantic), with `pipeline` reported
directly after `config`. The warning checks SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `difft` (present on PATH, probed
via `shutil.which` so the binary stays stdlib-only, reported directly
after `gh`; the warning detail SHALL name the semantic review's
text-engine degradation as the affected surface and the tiered
`semdiff doctor --fix` installer as the remedy, and a present binary
SHALL report `ok`), `textual` (importable), `pydantic`
(importable, probed via `importlib.util.find_spec` without importing it,
so the binary itself stays stdlib-only), `snapshot` (when the binary
runs from a plugin cache snapshot that is not the newest version
directory in the cache; when the binary runs from a repository checkout,
the check SHALL report dev mode as `ok`), and `statusline` (when the
Claude Code user settings file — default `~/.claude/settings.json` — is
absent or carries no `statusLine` key, probed read-only; the warning
detail SHALL name `shipd statusline install` as the remedy, and a
present registration SHALL report `ok`). The `pip install` hint on the
`textual` and `pydantic` details SHALL name `-r requirements.txt` when a
`requirements.txt` exists at the working-directory root, and the pinned
package specifier (`'textual>=8.2.8,<9'` / `'pydantic>=2.12,<3'`)
otherwise — a vendored per-repo install has no checkout to `-r` from.
Where the running interpreter is externally managed (PEP 668) — probed
read-only via the `EXTERNALLY-MANAGED` marker file in the interpreter's
stdlib directory resolved through `sysconfig` — the hint SHALL prepend
`--user --break-system-packages` to either form, so the printed command
is runnable by the interpreter that printed it; on an unmanaged
interpreter both hint forms SHALL remain unchanged. The
`pydantic` check SHALL stay `warn` when pydantic is not importable and no
declared pipeline requires it, and SHALL escalate to `fail` — naming the
supplying config path — when the resolved configuration declares an
`autonomous-pipeline` whose validation requires pydantic: a list value,
or a known preset name other than `default`. An absent key, the
`default` preset, an unknown preset name, or an unresolvable
configuration SHALL NOT escalate it. The verb SHALL mutate nothing.

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
- **THEN** a `warn difft — ` line names the review's text-engine degradation
  and the `semdiff doctor --fix` remedy, and the exit code is `0`

#### Scenario: Present difft reports ok
- **WHEN** `shipd doctor` runs with `difft` on PATH
- **THEN** the `difft` check line begins `ok`

#### Scenario: Missing textual only warns
- **WHEN** `shipd doctor` runs without `textual` importable, all required
  checks passing
- **THEN** a `warn textual — ` line names the board as the only affected
  surface and the exit code is `0`

#### Scenario: Missing pydantic only warns without a declared pipeline
- **WHEN** `shipd doctor` runs without `pydantic` importable on an unmanaged
  interpreter in a repo whose configuration declares no
  `autonomous-pipeline`, all required checks passing, with a
  `requirements.txt` at the working-directory root
- **THEN** a `warn pydantic — ` line names declared-pipeline validation as
  the only affected surface with a `pip install -r requirements.txt` hint
  and the exit code is `0`

#### Scenario: Missing requirements.txt pins the hint
- **WHEN** `shipd doctor` runs without `pydantic` importable on an unmanaged
  interpreter in a repo whose root carries no `requirements.txt`
- **THEN** the `pydantic` detail's hint names `pip install
  'pydantic>=2.12,<3'` and never `-r requirements.txt`

#### Scenario: Externally managed interpreter flags the checkout hint
- **WHEN** `shipd doctor` runs without `pydantic` importable on an
  externally managed interpreter (the `EXTERNALLY-MANAGED` marker present)
  in a repo with a `requirements.txt` at its root
- **THEN** the `pydantic` detail's hint names
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
  key holds a command
- **THEN** the `statusline` check line begins `ok`

#### Scenario: Resolvable pipeline reports its provenance
- **WHEN** `shipd doctor` runs in a repo whose effective pipeline resolves
  (a declared list or preset, or no declaration at all)
- **THEN** an `ok pipeline — ` line names the resolved entry count and the
  provenance (`default` when no layer declares the key)

#### Scenario: Unresolvable declared pipeline fails the preflight
- **WHEN** `shipd doctor` runs in a repo declaring an `autonomous-pipeline`
  that cannot resolve — malformed entries, an unknown preset, or a
  declaration requiring pydantic while it is not importable
- **THEN** a `fail pipeline — ` line carries the resolver's own error line
  and the exit code is `1`

#### Scenario: Declared pipeline escalates missing pydantic
- **WHEN** `shipd doctor` runs without `pydantic` importable on an unmanaged
  interpreter in a repo whose configuration declares an
  `autonomous-pipeline` list (or a known preset other than `default`), with
  a `requirements.txt` at the working-directory root
- **THEN** a `fail pydantic — ` line names the supplying config path with
  the `pip install -r requirements.txt` hint and the exit code is `1`

#### Scenario: Default preset never escalates pydantic
- **WHEN** `shipd doctor` runs without `pydantic` importable in a repo
  declaring `"autonomous-pipeline": "default"`
- **THEN** the `pipeline` line is `ok`, the `pydantic` line is `warn`, and
  the exit code is `0`

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
the newest snapshot's `integrations/statusline.sh`. If the settings file
already carries a `statusLine` entry whose command differs, then `install`
SHALL refuse with exit `1` naming the existing command unless `--force` is
given; an identical existing registration SHALL succeed idempotently. If
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

#### Scenario: Different existing registration refuses without force
- **WHEN** `install` runs against a settings file whose `statusLine.command`
  differs and `--force` is absent
- **THEN** the verb exits `1` naming the existing command and the file is
  unchanged; with `--force` the entry is replaced and the exit code is `0`

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
(default: the working directory), managing exactly four files:
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
the verb SHALL be read-only and exit `0`, printing one state per managed
file — `installed` (marker at the plugin version and, for the skill, a
byte-identical `semdiff.py`), `stale` (an older marker version or a
differing `semdiff.py`), `foreign`, or `absent` — plus a note that automatic
review is enabled through a GitHub branch ruleset and that the Copilot
code-review surface exposes no repository-side model selection. When invoked
as `copilot add`, the verb SHALL write all four files atomically
(same-directory temporary file and rename, parent directories created),
refreshing files it owns so a repeated `add` is idempotent and upgrades
stale installs; if any managed path is foreign, then `add` SHALL refuse with
exit `1` naming that file and write nothing, unless `--force` is given. When
invoked as `copilot remove`, the verb SHALL delete the managed files it
owns, remove the `.github/skills/code-review` directory tree only when
emptied, and succeed at exit `0` when files are already absent; if a managed
path is foreign, then `remove` SHALL refuse with exit `1` naming that file
and delete nothing, unless `--force` is given. The verb SHALL never invoke
`gh`, touch the network, or modify anything outside the four managed paths.

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

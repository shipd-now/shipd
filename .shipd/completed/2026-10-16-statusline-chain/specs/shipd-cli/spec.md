## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Statusline registration verb
id: statusline-verb
base: ce4f05209abe
Dropped: Different existing registration refuses without force

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

### Requirement: Doctor preflight verb
id: doctor-verb
base: 7b776fa09544

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
SHALL name `shipd statusline install` as the remedy, and a registration
containing `integrations/statusline.sh` SHALL report `ok`). The `pip install` hint on the
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

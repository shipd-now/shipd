## MODIFIED Requirements

### Requirement: Curated verb dispatch
id: cli-dispatch
base: 0cfdeff5f9f5

The `shipd` binary SHALL expose exactly the curated verbs `list`, `status`,
`locate`, `epic`, `workspace`, `board`, `metrics`, `lint`, `doctor`, and
`statusline`, and for every verb except `list`, `doctor`, and `statusline`
SHALL delegate by replacing its own process with the mapped engine script
invocation (`status` → `spec_status.py show`, `locate` →
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

#### Scenario: Statusline is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `statusline` among the verbs

### Requirement: Doctor preflight verb
id: doctor-verb
base: a2d680daef82

The `shipd` binary SHALL provide a read-only `doctor` verb that runs
environment preflight checks and prints one `ok <check> — <detail>`,
`warn <check> — <detail>`, or `fail <check> — <detail>` line per check
followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line, and
SHALL exit `1` if any required check fails and `0` otherwise. The required
checks SHALL be: `python` (interpreter at least 3.9), `git` (present on
PATH), and `config` (a resolvable layered configuration at the working
directory; a missing content directory is reported `ok` with a note). The
warning checks — never affecting the exit code — SHALL be: `gh` (present on
PATH and `gh auth status` exiting 0), `textual` (importable), `pydantic`
(importable, probed via `importlib.util.find_spec` without importing it, so
the binary itself stays stdlib-only), `snapshot` (when the binary runs
from a plugin cache snapshot that is not the newest version directory in the
cache; when the binary runs from a repository checkout, the check SHALL
report dev mode as `ok`), and `statusline` (when the Claude Code user
settings file — default `~/.claude/settings.json` — is absent or carries no
`statusLine` key, probed read-only; the warning detail SHALL name
`shipd statusline install` as the remedy, and a present registration SHALL
report `ok`). The verb SHALL mutate nothing.

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

#### Scenario: Missing pydantic only warns
- **WHEN** `shipd doctor` runs without `pydantic` importable, all required
  checks passing
- **THEN** a `warn pydantic — ` line names declared-pipeline validation as
  the only affected surface with a `pip install -r requirements.txt` hint
  and the exit code is `0`

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

## ADDED Requirements

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

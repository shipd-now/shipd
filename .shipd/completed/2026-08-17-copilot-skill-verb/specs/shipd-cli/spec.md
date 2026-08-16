## MODIFIED Requirements

### Requirement: Curated verb dispatch
id: cli-dispatch
base: b20dd563f860

The `shipd` binary SHALL expose exactly the curated verbs `list`, `status`,
`locate`, `epic`, `workspace`, `board`, `metrics`, `lint`, `doctor`,
`statusline`, and `copilot`, and for every verb except `list`, `doctor`,
`statusline`, and `copilot` SHALL delegate by replacing its own process with
the mapped engine script invocation (`status` -> `spec_status.py show`,
`locate` -> `spec_status.py locate`, `epic` -> `spec_status.py epic-show`,
`workspace` -> `spec_status.py workspace-show`, `board` -> `dashboard.py` per
the board-mode mapping below, `metrics` -> `metrics.py`, `lint` ->
`spec_lint.py`), passing all trailing arguments through verbatim so the
delegate's output and exit code are the binary's own. When `metrics` is given
no trailing arguments, the binary SHALL delegate to `metrics.py summary`.
When invoked as `shipd board`, the binary SHALL select the delegate by the
first trailing argument: the bare word `text` SHALL be consumed and delegate
to `dashboard.py board`, and any other first trailing argument (or none)
SHALL delegate to `dashboard.py tui` with all trailing arguments intact. The
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

#### Scenario: Copilot is a curated verb
- **WHEN** `shipd --help` runs
- **THEN** the usage banner lists `copilot` among the verbs

## ADDED Requirements

### Requirement: Copilot review-skill maintenance verb
id: copilot-verb

The `shipd` binary SHALL provide a `copilot` verb that maintains the shipd
Copilot code-review skill in a target repository rooted at `--root DIR`
(default: the working directory), managing exactly three files:
`.github/skills/code-review/SKILL.md` and
`.github/skills/code-review/scripts/semdiff.py` and
`.github/workflows/copilot-code-review.yml`. The SKILL.md and workflow
content SHALL come from the plugin's `integrations/copilot/` templates,
resolved relative to the binary's own location, with the `{version}`
placeholder in each template's ownership marker (`<!-- shipd-copilot
v{version} -->` in SKILL.md, `# shipd-copilot v{version}` in the workflow)
replaced by the plugin manifest version; the installed `semdiff.py` SHALL be
a byte-identical copy of the plugin's `skills/review/scripts/semdiff.py` and
carries no marker of its own. A marker-bearing managed file (the SKILL.md or
the workflow) that exists without its ownership marker SHALL be treated as
foreign; an existing `semdiff.py` SHALL be treated as owned exactly when the
adjacent SKILL.md is owned, and as foreign otherwise. When invoked bare, the verb SHALL be read-only and exit `0`,
printing one state per managed file — `installed` (marker at the plugin
version and, for the skill, a byte-identical `semdiff.py`), `stale` (an older
marker version or a differing `semdiff.py`), `foreign`, or `absent` — plus a
note that automatic review is enabled through a GitHub branch ruleset and
that the Copilot code-review surface exposes no repository-side model
selection. When invoked as `copilot add`, the verb SHALL write all three
files atomically (same-directory temporary file and rename, parent
directories created), refreshing files it owns so a repeated `add` is
idempotent and upgrades stale installs; if any managed path is foreign, then
`add` SHALL refuse with exit `1` naming that file and write nothing, unless
`--force` is given. When invoked as `copilot remove`, the verb SHALL delete
the managed files it owns, remove the `.github/skills/code-review` directory
tree only when emptied, succeed at exit `0` when files are already absent;
if a managed path is foreign, then `remove` SHALL refuse with exit `1`
naming that file and delete nothing, unless `--force` is given. The verb
SHALL never invoke `gh`, touch the network, or modify anything outside the
three managed paths.

#### Scenario: Bare report on an empty repository
- **WHEN** `shipd copilot --root <dir>` runs against a directory with no
  managed files
- **THEN** every managed file reports `absent`, nothing is created, and the
  exit code is `0`

#### Scenario: Add installs the three managed files
- **WHEN** `shipd copilot add --root <dir>` runs against an empty directory
- **THEN** the SKILL.md and workflow land with their markers carrying the
  plugin manifest version, `semdiff.py` is byte-identical to the plugin's
  copy, and the exit code is `0`

#### Scenario: Repeated add refreshes a stale install
- **WHEN** `add` runs against a repo whose installed SKILL.md marker names an
  older version
- **THEN** the files are rewritten at the current version and the exit code
  is `0`

#### Scenario: Add refuses a foreign file without force
- **WHEN** `add` runs and `.github/workflows/copilot-code-review.yml` exists
  without the ownership marker and `--force` is absent
- **THEN** the verb exits `1` naming that file and no managed file is written;
  with `--force` the file is replaced and the exit code is `0`

#### Scenario: Remove deletes only what it owns
- **WHEN** `shipd copilot remove --root <dir>` runs against a marked install
- **THEN** the three managed files are deleted, the emptied
  `.github/skills/code-review` tree is pruned, and the exit code is `0`

#### Scenario: Remove refuses a foreign file without force
- **WHEN** `remove` runs and the installed SKILL.md carries no ownership
  marker and `--force` is absent
- **THEN** the verb exits `1` naming that file and deletes nothing

#### Scenario: Report distinguishes stale from installed
- **WHEN** the installed `semdiff.py` differs from the plugin's copy and the
  bare verb runs
- **THEN** the skill's report line is `stale` and the exit code is `0`

## MODIFIED Requirements

### Requirement: Copilot review-skill maintenance verb
id: copilot-verb
base: c979c80aabe7

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

## ADDED Requirements

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

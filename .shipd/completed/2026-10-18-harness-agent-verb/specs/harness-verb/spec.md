## MODIFIED Requirements

### Requirement: Generation actions
id: harness-add-remove
base: 4ae6182f05a3

The `shipd harness` verb SHALL provide `add` and `remove` actions taking one or
more harness ids or `--all`, a `--root DIR` selecting repo surfaces, and
`--user` selecting user-global surfaces. `add` SHALL write one generated file
per command into the registry-declared path, including command-specific
directories declared through `{command}` in `user_dir`, and SHALL render each
body with the harness's declared features.

For a harness declaring `file-references`, `add` SHALL write fallback references
under the mode's reference root. A `conventions-file` harness SHALL instead
write one conventions file and report its wiring step. Every generated file
SHALL carry the ownership marker. Foreign targets SHALL be refused unless
`--force`; unchanged reruns SHALL preserve bytes and modification times.

For a harness whose registry entry carries an `agent` member, `add` SHALL also
write one agent file per `AGENT_ROLES` member at the entry's agent repo or user
path, and `remove` SHALL delete those agent files with the command files. An
agent file SHALL carry the ownership marker and SHALL obey the same
foreign-target and `--force` rules as a command file; a harness whose `agent`
member is `None` SHALL gain no agent file. `shipd install` SHALL write the agent
files for every selected harness that carries an agent surface.

Where the registry declares legacy user patterns, successful user-mode `add` and
`remove` SHALL delete legacy files only when they carry shipd's ownership
marker. A foreign legacy file SHALL remain unchanged and SHALL NOT block writing
or removing the current surface. `remove` SHALL delete only eligible generated
files and directories it empties. Unsupported surfaces SHALL be skipped
successfully, and all actions SHALL remain offline.

#### Scenario: Add generates owned files for a repo-level harness
- **WHEN** `shipd harness add cursor --root <tmp>` runs in a temp repo
- **THEN** `.cursor/commands/` holds one owned `shipd-<command>.md` per body
  template, and an unchanged rerun changes no bytes

#### Scenario: AGY repo mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --root <tmp>` runs
- **THEN** each command is written under `.agents/skills/shipd-<command>/SKILL.md`
  with `name` and `description` frontmatter

#### Scenario: File-references harnesses get reference files
- **WHEN** `shipd harness add cursor --root <tmp>` runs
- **THEN** fallback references exist under `<content-dir>/harness/references/`
  and generated bodies name that root

#### Scenario: User mode writes the user-global surface
- **WHEN** `shipd harness add codex --user` runs with an isolated `HOME`
- **THEN** generated files land under `~/.codex/prompts/` and nothing is written
  under the working directory

#### Scenario: AGY user mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --user` runs with an isolated `HOME`
- **THEN** each command is written under `~/.gemini/config/skills/shipd-<command>/SKILL.md`

#### Scenario: AGY add migrates owned legacy files
- **GIVEN** marker-owned AGY files exist under `~/.gemini/antigravity-cli/skills/`
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the marker-owned legacy
  files are deleted

#### Scenario: AGY migration preserves foreign legacy files
- **GIVEN** an unmarked file exists at an AGY legacy path
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the foreign legacy file
  remains byte-identical

#### Scenario: Aider gets exactly one conventions file
- **WHEN** `shipd harness add aider --root <tmp>` runs
- **THEN** exactly one owned `shipd-conventions.md` is written and the report
  names the `.aider.conf.yml` wiring step

#### Scenario: A modeless harness is skipped, not failed
- **WHEN** `shipd harness add aider --user` runs with an isolated `HOME`
- **THEN** the action exits 0, reports aider as skipped, and writes no file

#### Scenario: Foreign files are refused without force
- **WHEN** a current target exists without the marker and `add` runs without
  `--force`
- **THEN** one `Error:` line names the target, the action exits nonzero, and the
  file remains unchanged

#### Scenario: Remove deletes only owned files
- **WHEN** `shipd harness remove cursor --root <tmp>` runs after add with an
  unmarked neighbor
- **THEN** generated files are gone, the unmarked neighbor remains, and emptied
  directories are pruned

#### Scenario: AGY remove cleans current and legacy owned files
- **GIVEN** current AGY packages and marker-owned legacy files exist in user mode
- **WHEN** `shipd harness remove agy --user` runs
- **THEN** both generated surfaces are removed while unmarked legacy files remain

#### Scenario: Add writes the agent files beside the commands
- **WHEN** `shipd harness add claude-code --user` runs with an isolated `HOME`
- **THEN** `~/.claude/agents/` holds one owned `shipd-<role>.md` per
  `AGENT_ROLES` member, each carrying the ownership marker, and
  `shipd harness add cursor --user` writes no agent file

#### Scenario: Remove deletes the agent files
- **WHEN** `shipd harness remove claude-code --user` runs after add
- **THEN** the agent files are gone along with the command files

#### Scenario: A foreign agent file is refused without force
- **GIVEN** an unmarked file sits at a harness's agent path
- **WHEN** `shipd harness add <harness> --user` runs without `--force`
- **THEN** one `Error:` line names the agent path, the action exits nonzero, and
  the file remains unchanged

### Requirement: Installation state report
id: harness-status
base: 415251f33c08

The `shipd harness` verb SHALL provide a read-only `status` action taking
optional harness ids (default: all), `--root DIR`, `--user`, and `--json`,
reporting per harness and surface one of `installed` (every expected file
present and byte-identical to a fresh render), `stale` (present but differing),
`foreign` (a target exists without the ownership marker), or `absent`. The
expected and present counts SHALL include the harness's agent files when its
entry carries an `agent` member, so a harness is `installed` only when its
command and agent files are both byte-current. The action SHALL create or modify
no files.

#### Scenario: Status reflects the lifecycle
- **WHEN** `status` runs before an `add`, after it, and after one generated file
  is edited in place
- **THEN** the harness reports `absent`, then `installed`, then `stale`, and the
  temp root's contents are unchanged by every `status` run

#### Scenario: JSON status is machine-readable
- **WHEN** `shipd harness status --root <tmp> --json` runs
- **THEN** stdout parses as one JSON document keyed by harness id

#### Scenario: Status counts the agent files
- **WHEN** `status` runs for `claude-code` after `add` writes its agent files,
  then after one agent file is deleted
- **THEN** the harness reports `installed`, then `stale` naming the missing
  agent file

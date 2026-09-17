## MODIFIED Requirements

### Requirement: Generation actions
id: harness-add-remove
base: 462d187ee71e

The `shipd harness` verb SHALL provide `add` and `remove` actions taking one or more harness ids or `--all`, a `--root DIR` selecting repo surfaces, and `--user` selecting user-global surfaces. `add` SHALL write one generated file per command into the registry-declared path, including command-specific directories declared through `{command}` in `user_dir`, and SHALL render each body with the harness's declared features.

For a harness declaring `file-references`, `add` SHALL write fallback references under the mode's reference root. A `conventions-file` harness SHALL instead write one conventions file and report its wiring step. Every generated file SHALL carry the ownership marker. Foreign targets SHALL be refused unless `--force`; unchanged reruns SHALL preserve bytes and modification times.

Where the registry declares legacy user patterns, successful user-mode `add` and `remove` SHALL delete legacy files only when they carry shipd's ownership marker. A foreign legacy file SHALL remain unchanged and SHALL NOT block writing or removing the current surface. `remove` SHALL delete only eligible generated files and directories it empties. Unsupported surfaces SHALL be skipped successfully, and all actions SHALL remain offline.

#### Scenario: Add generates owned files for a repo-level harness
- **WHEN** `shipd harness add cursor --root <tmp>` runs in a temp repo
- **THEN** `.cursor/commands/` holds one owned `shipd-<command>.md` per body template, and an unchanged rerun changes no bytes

#### Scenario: AGY repo mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --root <tmp>` runs
- **THEN** each command is written under `.agents/skills/shipd-<command>/SKILL.md` with `name` and `description` frontmatter

#### Scenario: File-references harnesses get reference files
- **WHEN** `shipd harness add cursor --root <tmp>` runs
- **THEN** fallback references exist under `<content-dir>/harness/references/` and generated bodies name that root

#### Scenario: User mode writes the user-global surface
- **WHEN** `shipd harness add codex --user` runs with an isolated `HOME`
- **THEN** generated files land under `~/.codex/prompts/` and nothing is written under the working directory

#### Scenario: AGY user mode writes Agent Skills packages
- **WHEN** `shipd harness add agy --user` runs with an isolated `HOME`
- **THEN** each command is written under `~/.gemini/config/skills/shipd-<command>/SKILL.md`

#### Scenario: AGY add migrates owned legacy files
- **GIVEN** marker-owned AGY files exist under `~/.gemini/antigravity-cli/skills/`
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the marker-owned legacy files are deleted

#### Scenario: AGY migration preserves foreign legacy files
- **GIVEN** an unmarked file exists at an AGY legacy path
- **WHEN** `shipd harness add agy --user` runs
- **THEN** current Agent Skills packages are written and the foreign legacy file remains byte-identical

#### Scenario: Aider gets exactly one conventions file
- **WHEN** `shipd harness add aider --root <tmp>` runs
- **THEN** exactly one owned `shipd-conventions.md` is written and the report names the `.aider.conf.yml` wiring step

#### Scenario: A modeless harness is skipped, not failed
- **WHEN** `shipd harness add aider --user` runs with an isolated `HOME`
- **THEN** the action exits 0, reports aider as skipped, and writes no file

#### Scenario: Foreign files are refused without force
- **WHEN** a current target exists without the marker and `add` runs without `--force`
- **THEN** one `Error:` line names the target, the action exits nonzero, and the file remains unchanged

#### Scenario: Remove deletes only owned files
- **WHEN** `shipd harness remove cursor --root <tmp>` runs after add with an unmarked neighbor
- **THEN** generated files are gone, the unmarked neighbor remains, and emptied directories are pruned

#### Scenario: AGY remove cleans current and legacy owned files
- **GIVEN** current AGY packages and marker-owned legacy files exist in user mode
- **WHEN** `shipd harness remove agy --user` runs
- **THEN** both generated surfaces are removed while unmarked legacy files remain

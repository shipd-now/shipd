## ADDED Requirements

### Requirement: The /s:init skill and its sections
id: init-skill-sections

The plugin SHALL ship a skill named `init` with a harness body
`harness/bodies/init.md`. Bare `/s:init` SHALL run the full wizard;
`/s:init <section>` SHALL run one section alone, where the sections are
`layout`, `config`, `workspace`, `wiki`, `memory`, `hooks`, and `gate`. If the
section is not one of these, then the skill SHALL list the sections and stop
without writing. `README.md`, `docs/cheatsheet.md`, and `AGENTS.md` SHALL list
`/s:init`.

#### Scenario: Unknown section writes nothing
- **WHEN** `/s:init colours` runs
- **THEN** the skill lists the seven sections and no file changes

#### Scenario: Registry files list the command
- **WHEN** `README.md`, `docs/cheatsheet.md`, and `AGENTS.md` are read
- **THEN** each names `/s:init`

### Requirement: The setup wizard
id: init-wizard-steps

The wizard SHALL run its steps in the order of `artefacts/wizard-keys.md`:
where files live (`dir`, `store_root`), how changes ship (`pr-mode`,
`autonomous-pipeline`), personal stores (`memory_dir`, `wiki_base`), session
behaviour (`voice`, `guardrails`), then the constitution. It SHALL ask one
AskUserQuestion per key, listing the key's current value (or its default) first.
The bare wizard SHALL skip every key that `shipd config` reports with a file
provenance; a section run alone SHALL ask every key in that section. Every
answer SHALL be written through `shipd config set <key> <value>`, except a
default that is the key's absence, which writes nothing. The where-files-live
step SHALL end by running `spec_status.py init`. If `shipd config set` exits
1, then the skill SHALL relay its `error:` and `hint:` lines. Where every
`error:` line names the key being set, the skill SHALL ask that key once more.
Where an `error:` line names a different key, the skill SHALL offer to fix
that key first, through its own dialog and `shipd config set`, then retry the
original key once; it SHALL NOT re-ask the original key in a loop. The skill SHALL NOT edit any `.shipd-config.json` by hand. While
`spec_status.py init-status` reports `unattended: true`, the skill SHALL open
no dialog and SHALL run only `spec_status.py init`.

#### Scenario: Declared keys are skipped
- **GIVEN** the repo layer declares `"pr-mode": "draft"`
- **WHEN** bare `/s:init` runs
- **THEN** no `pr-mode` dialog opens and the other unset keys are asked

#### Scenario: A config section re-asks only config keys
- **GIVEN** a project whose layout exists and whose repo layer declares
  `pr-mode`
- **WHEN** `/s:init config` runs
- **THEN** dialogs open for the six config keys only, the `pr-mode` dialog
  lists `draft` first, and no `dir` or `store_root` dialog opens

#### Scenario: Rejected value is re-asked
- **WHEN** the user types `bogus` for `pr-mode` and `shipd config set` exits 1
- **THEN** the skill shows the `hint: accepted values: auto, draft` line and
  asks `pr-mode` once more

#### Scenario: Another invalid key is fixed first
- **GIVEN** the user layer declares `"pr-mode": "bogus"`
- **WHEN** the user answers `voice` and `shipd config set voice false` exits 1
  with an `error:` line naming `pr-mode`
- **THEN** the skill relays the lines, opens a `pr-mode` dialog, and retries
  `voice` once after `pr-mode` is set

#### Scenario: Unattended runs only the scaffold
- **GIVEN** `SHIPD_UNATTENDED=1`
- **WHEN** `/s:init` runs on a first-run repository
- **THEN** no dialog opens and `spec_status.py init` creates the layout

### Requirement: Constitution starter in the wizard only
id: init-constitution-starter

The wizard's last step SHALL offer the starter
`skills/init/references/constitution-starter.md` only when the content
directory holds no `constitution.md`, and on acceptance SHALL copy it there.
No section run and no needs-setup scaffold SHALL write a `constitution.md`, and
the skill SHALL NOT overwrite an existing one. The starter SHALL be a
commented template whose example rules sit inside HTML comments.

#### Scenario: Existing constitution is kept
- **GIVEN** the content directory already holds `constitution.md`
- **WHEN** bare `/s:init` runs
- **THEN** no constitution dialog opens and the file is unchanged

#### Scenario: Section runs never write one
- **WHEN** `/s:init config` runs on a project with no `constitution.md`
- **THEN** no `constitution.md` is created

### Requirement: Hand-off sections
id: init-handoff-sections

The `workspace` section SHALL run `shipd workspace` and, when no workspace
resolves, ask one path dialog and run `spec_status.py workspace-init <path>`;
`wiki` SHALL run `spec_status.py wiki-init`; `memory` SHALL run
`spec_status.py wiki-init --personal`; `hooks` SHALL hand off to
`/s:worktree-hooks` and `gate` to `/s:gate` by reference. The skill SHALL
relay each verb's output and SHALL NOT restate the handed-off skill's steps.

#### Scenario: Memory section scaffolds the personal store
- **WHEN** `/s:init memory` runs with no personal store
- **THEN** `spec_status.py wiki-init --personal` runs and its output is relayed

### Requirement: Shared needs-setup reference
id: needs-setup-reference

`skills/init/references/needs-setup.md` SHALL tell a skill to run
`spec_status.py init-status` from the root it writes into, adding
`--unattended` when its invocation says no human is available or the run is
unattended, and to act on the `action:` line: `none` continues; `scaffold`
runs `spec_status.py init`, prints one line, and continues; `wizard` runs the
`/s:init` wizard and continues once `init-status` reports `action: none`. If
`init-status` exits non-zero, then the skill SHALL relay the `Error:` line and
stop. Under harness plan mode the skill SHALL report the verdict and stop
before scaffolding.

#### Scenario: Ready project does nothing
- **GIVEN** `init-status` prints `action: none`
- **WHEN** a skill runs the check
- **THEN** it prints nothing about setup and continues

#### Scenario: Malformed config stops the skill
- **GIVEN** the repo's `.shipd-config.json` is not valid JSON
- **WHEN** a skill runs the check
- **THEN** it relays the `Error:` line and stops

### Requirement: Layout-requiring skills route through the reference
id: needs-setup-roster

The SKILL.md and harness body of `plan`, `epic`, `research`, `autopilot`,
`status`, `initiative`, and `build` SHALL each name
`skills/init/references/needs-setup.md` and SHALL NOT carry their former
missing-layout handling (stop-on-missing, scaffold-or-stop, or the claim that
the layout appears when a change is first merged).

#### Scenario: Every roster skill points at the reference
- **WHEN** the seven SKILL.md files and bodies are read
- **THEN** each contains `skills/init/references/needs-setup.md`

#### Scenario: Build no longer claims first-merge creation
- **WHEN** `plugins/s/skills/build/SKILL.md` is read
- **THEN** it does not contain `created the first time a change is merged`

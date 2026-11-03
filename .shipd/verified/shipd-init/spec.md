# shipd-init

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

The wizard SHALL cover its keys in this order: where files live (`dir`,
`store_root`), how changes ship (`pr-mode`, `autonomous-pipeline`), personal
stores (`memory_dir`, `wiki_base`), session behaviour (`voice`, `guardrails`),
then the constitution. It SHALL present them as one numbered settings sheet,
printed as plain response text in the layout of `artefacts/settings-sheet.md`,
with each line showing the key's current value (or its default). It SHALL
collect the answers from one typed reply and SHALL NOT open an AskUserQuestion
for any key. A reply of `ok` SHALL accept every line; a reply of `<n> <value>`
pairs SHALL change only the named lines. The bare wizard SHALL list every key
that `shipd config` reports with a file provenance in an unnumbered
`Already set (kept):` block and SHALL number only the unset keys; a section run
alone SHALL number every key in that section. If a reply names a line outside
the sheet or fits no reply form, then the skill SHALL re-print the sheet once
with a note, and on a second such reply SHALL stop with nothing written.

Every answer SHALL be written through `shipd config set <key> <value>`, except
a default that is the key's absence, which writes nothing. The skill SHALL
write the `dir` and `store_root` lines first, then run `spec_status.py init`,
then write the remaining lines. If `shipd config set` exits 1, then the skill
SHALL relay its `error:` and `hint:` lines and SHALL continue with the other
lines. When any line failed, the skill SHALL print one retry sheet holding
only the failed lines, plus a line for any other key an `error:` line names,
written before the failed keys are retried. A line that fails again SHALL be
skipped with a note; the skill SHALL NOT print a second retry sheet. The
skill SHALL NOT edit any `.shipd-config.json` by hand. While
`spec_status.py init-status` reports `unattended: true`, the skill SHALL print
no sheet and SHALL run only `spec_status.py init`.

#### Scenario: One sheet replaces the dialogs
- **GIVEN** a fresh project with no config layer declaring any wizard key
- **WHEN** bare `/s:init` runs
- **THEN** one numbered sheet of nine lines prints with each default shown,
  and no AskUserQuestion opens

#### Scenario: Accepting the sheet writes the defaults
- **WHEN** the user replies `ok` to the fresh-project sheet
- **THEN** `shipd config set` runs for `dir`, `pr-mode`,
  `autonomous-pipeline`, `memory_dir`, and `voice`, and not for `store_root`,
  `wiki_base`, or `guardrails`

#### Scenario: Named lines change, the rest keep their default
- **WHEN** the user replies `3 draft, 7 false` to the fresh-project sheet
- **THEN** `pr-mode` is written as `draft`, `voice` as `false`, and every
  other line takes its shown default

#### Scenario: Declared keys are kept, not numbered
- **GIVEN** the repo layer declares `"pr-mode": "draft"`
- **WHEN** bare `/s:init` runs
- **THEN** `pr-mode` appears under `Already set (kept):` with no line number,
  and only the unset keys are numbered

#### Scenario: A config section numbers only config keys
- **GIVEN** a project whose layout exists and whose repo layer declares
  `pr-mode`
- **WHEN** `/s:init config` runs
- **THEN** the sheet numbers the six config keys, the `pr-mode` line shows
  `draft`, and no `dir` or `store_root` line appears

#### Scenario: Rejected value gets one retry sheet
- **WHEN** the user replies `3 bogus` and `shipd config set pr-mode bogus`
  exits 1
- **THEN** the skill shows the `hint: accepted values: auto, draft` line,
  writes the other lines, and prints a retry sheet holding only the
  `pr-mode` line

#### Scenario: Another invalid key joins the retry sheet
- **GIVEN** the user layer declares `"pr-mode": "bogus"`
- **WHEN** `shipd config set voice false` exits 1 with an `error:` line naming
  `pr-mode`
- **THEN** the retry sheet holds a `pr-mode` line and a `voice` line, and
  `pr-mode` is written before `voice` is retried once

#### Scenario: Unparseable reply re-prints once
- **WHEN** the user replies `12 foo` to a nine-line sheet
- **THEN** the sheet re-prints once with a note naming line 12, and nothing
  is written yet

#### Scenario: Unattended runs only the scaffold
- **GIVEN** `SHIPD_UNATTENDED=1`
- **WHEN** `/s:init` runs on a first-run repository
- **THEN** no sheet prints and `spec_status.py init` creates the layout

### Requirement: Constitution starter in the wizard only
id: init-constitution-starter

The wizard's sheet SHALL carry a `constitution` line offering the starter
`skills/init/references/constitution-starter.md` only when the content
directory holds no `constitution.md`, and when that line is accepted SHALL copy
the starter there. No section run and no needs-setup scaffold SHALL write a
`constitution.md`, and the skill SHALL NOT overwrite an existing one. The
starter SHALL be a commented template whose example rules sit inside HTML
comments.

#### Scenario: Existing constitution is kept
- **GIVEN** the content directory already holds `constitution.md`
- **WHEN** bare `/s:init` runs
- **THEN** the sheet carries no constitution line and the file is unchanged

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

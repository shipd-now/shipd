## MODIFIED Requirements

### Requirement: The setup wizard
id: init-wizard-steps
base: ddd1967528f6
Dropped: Declared keys are skipped
Dropped: A config section re-asks only config keys
Dropped: Rejected value is re-asked
Dropped: Another invalid key is fixed first

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
base: 7dd8667d3ec0

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

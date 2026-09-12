## MODIFIED Requirements

### Requirement: Command cheatsheet
id: cheatsheet-doc
base: 65b166a7c679

`docs/cheatsheet.md` SHALL be a lookup reference opening with a
`<!-- doc-type: reference -->` comment on its first line, totalling 250
lines or fewer and passing `docs_lint.py`, listing every user-facing command
in two tables — one for the `/s:` commands, one for the `shipd` CLI verbs.
Each row SHALL carry the invocation including its argument and option forms,
a one-line description of what the command does, and exactly one short
example invocation. The `/s:` table SHALL carry one row for every directory
under `plugins/s/skills/`, and the `shipd` table SHALL carry one row for
every verb listed in the `shipd --help` banner. Where an option is accepted
by several verbs, the cheatsheet SHALL state it once in a conventions
preamble rather than repeating it on every row. Where a verb requires a
precondition this repository does not meet, its row SHALL name that
precondition rather than omit the verb or invent an invocation that avoids
it.

The file SHALL additionally carry exactly one mermaid diagram: a `venn-beta`
fence, above the `/s:` table and under its own level-2 heading, whose three
sets are the `README.md` **Skills** groups — the core loop, bigger than one
change, and knowledge. Every directory under `plugins/s/skills/` SHALL appear
in that diagram exactly once as `s:<name>`, in the region for the group or
groups it spans, and each region SHALL hold exactly one `text` node listing
its names. The fence SHALL carry no `title` line and no `style` line, so the
corpus states content and the rendering surface states presentation.

#### Scenario: Cheatsheet passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/cheatsheet.md` runs
- **THEN** it exits 0, the first line is the reference marker, and the file
  is at most 250 lines

#### Scenario: Every skill has a row
- **WHEN** the `/s:` table's rows are compared against the directory names
  under `plugins/s/skills/`
- **THEN** every directory has exactly one row and no row names a command
  that has no directory

#### Scenario: Every shipd verb has a row
- **WHEN** the `shipd` table's rows are compared against the verb list
  printed by `shipd --help`
- **THEN** every listed verb has exactly one row and no row names a verb the
  banner does not list

#### Scenario: Each row carries one example
- **WHEN** a reader scans any row of either table
- **THEN** that row shows the invocation with its argument and option forms,
  a one-line description, and exactly one example invocation

#### Scenario: Read-only examples run as written
- **WHEN** the read-only examples in the `shipd` table whose rows name no
  precondition are executed verbatim from the repository root
- **THEN** each one runs and exits zero

#### Scenario: A precondition-gated row names its precondition
- **WHEN** a reader scans the row for a verb that cannot succeed here
  without setup — `workspace`, which resolves through the nearest ancestor
  `.shipd-config.json` declaring a `workspace` key
- **THEN** the row names that precondition, and its example is still the
  ordinary invocation rather than one contrived to exit zero

#### Scenario: Shared flags are stated once
- **WHEN** a reader looks for what `--json` or `--root` mean
- **THEN** they are explained in the conventions preamble, and the per-verb
  rows do not repeat that explanation

#### Scenario: Every skill appears in the diagram exactly once
- **WHEN** the `s:<name>` tokens inside the `venn-beta` fence are collected
  and compared against the directory names under `plugins/s/skills/`
- **THEN** every directory appears exactly once and no token names a skill
  that has no directory

#### Scenario: The fence is content-only and singular
- **WHEN** `docs/cheatsheet.md` is read
- **THEN** it holds exactly one ```mermaid fence, that fence's first body
  line is `venn-beta`, and the fence carries no `title` line and no `style`
  line

#### Scenario: Each region carries one text node
- **WHEN** the fence's `set` and `union` declarations are read
- **THEN** each one is followed by exactly one indented `text` line

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills
base: 0e8ce0665aae

The `README.md` SHALL include a **Skills** section listing every skill in
the `s` plugin. Each skill entry SHALL state its invocation name
(`/s:<name>`) and a one-to-two sentence description consistent with that
skill's own `description` frontmatter. The section SHALL reflect the current
skill set exactly — no missing skills, no skills that do not exist, and no
references to retired systems. Every skill SHALL appear under exactly one of
the section's three group headings — the core loop, bigger than one change,
and knowledge — so the section partitions the skill set rather than sampling
it.

#### Scenario: All current skills are documented
- **WHEN** the Skills section is compared against the plugin's skill
  directories
- **THEN** every skill appears with its `/s:<name>` invocation and a
  description consistent with its frontmatter

#### Scenario: No stale entries
- **WHEN** the Skills section is read
- **THEN** it names no skill that does not exist and no retired system

#### Scenario: The three groups partition the skill set
- **WHEN** the rows of the section's three group tables are collected
- **THEN** each directory under `plugins/s/skills/` appears in exactly one
  of them, and no skill appears in two

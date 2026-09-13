## MODIFIED Requirements

### Requirement: Command cheatsheet
id: cheatsheet-doc
base: e8eaefedf284

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
change, and knowledge. Each of the fence's seven regions SHALL hold exactly
one `text` node naming what that region holds, in at most three words — and
in at most two for the three pairwise regions and the centre, whose area does
not carry more — and SHALL name no skill. The fence SHALL carry no `title` line and no `style`
line, so the corpus states content and the rendering surface states
presentation. Beneath the fence the file SHALL carry a list naming every
directory under `plugins/s/skills/` exactly once as `s:<name>`, grouped under
the region names the fence uses, so every skill the diagram places is legible
without reading the diagram.

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

#### Scenario: Every skill appears in the list exactly once
- **WHEN** the `s:<name>` tokens in the list beneath the fence are collected
  and compared against the directory names under `plugins/s/skills/`
- **THEN** every directory appears exactly once and no token names a skill
  that has no directory

#### Scenario: The fence names regions, not skills
- **WHEN** the `venn-beta` fence is read
- **THEN** each of its seven `set` and `union` declarations is followed by
  exactly one indented `text` line of at most three words, and no `text` line
  contains the string `s:`

#### Scenario: The fence is content-only and singular
- **WHEN** `docs/cheatsheet.md` is read
- **THEN** it holds exactly one ```mermaid fence, that fence's first body
  line is `venn-beta`, and the fence carries no `title` line and no `style`
  line

#### Scenario: Every region name reappears in the list
- **WHEN** the region names in the fence's `text` lines are compared against
  the bolded group names in the list beneath it
- **THEN** each of the seven region names appears in the list, so a reader
  moving from a circle to the list finds the same word

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills
base: 03cc4e57fe70

The `README.md` SHALL include a **Skills** section listing every skill in
the `s` plugin. Each skill entry SHALL state its invocation name
(`/s:<name>`) and a one-to-two sentence description consistent with that
skill's own `description` frontmatter. The section SHALL reflect the current
skill set exactly — no missing skills, no skills that do not exist, and no
references to retired systems. The section SHALL carry exactly three group
headings — **Pipeline**, **Orchestration** and **Memory** — and every skill
SHALL appear under exactly one of them, so the section partitions the skill
set rather than sampling it.

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

#### Scenario: The section's three headings are Pipeline, Orchestration and Memory
- **WHEN** the Skills section's group headings are read
- **THEN** they are exactly `**Pipeline**`, `**Orchestration**` and
  `**Memory**`, in that order

## ADDED Requirements

### Requirement: Getting-started guide
id: getting-started-doc

A `docs/getting-started.md` SHALL walk a newcomer through their first working
session in this order: registering the ☕ statusline, then taking one change
through `/s:plan` and `/s:build`. The guide SHALL explain each planning
artifact — `plan.md`, the per-capability delta `spec.md`, and `tasks.md` —
with its purpose, and SHALL name the three durable outcomes of a build: the
`change/<name>` branch, the merge into `verified/`, and the archive under
`completed/`. Where it documents statusline registration for an installed
plugin, the guide SHALL give a command that resolves the newest cached
snapshot rather than a version-pinned path. The guide SHALL link
`docs/cheatsheet.md` from its closing where-to-go-next section.

#### Scenario: Statusline precedes the walkthrough
- **WHEN** a reader follows `docs/getting-started.md` top to bottom
- **THEN** the statusline registration and its rendered segments are explained
  before the `/s:plan` walkthrough begins

#### Scenario: Artifacts are each explained
- **WHEN** the reader reaches the planning walkthrough
- **THEN** `plan.md`, the delta `specs/<capability>/spec.md`, and `tasks.md`
  are each explained with their purpose, and the delta's WHEN/THEN scenario
  grammar is shown in an excerpt

#### Scenario: Build outcomes are named
- **WHEN** the reader reaches the build walkthrough
- **THEN** the change branch, the `verified/` master-library merge, and the
  `completed/` archive are all named as the build's durable outcomes

#### Scenario: Install-mode registration survives updates
- **WHEN** the documented install-mode statusline command is executed with
  more than one snapshot in the plugin cache
- **THEN** it runs the newest snapshot's `integrations/statusline.sh` under
  dotted-version ordering, not a version-pinned path

#### Scenario: Guide points at the cheatsheet
- **WHEN** a reader reaches the guide's closing where-to-go-next section
- **THEN** a relative link to `cheatsheet.md` is present there

### Requirement: Command cheatsheet
id: cheatsheet-doc

A `docs/cheatsheet.md` SHALL be a lookup reference listing every user-facing
command in two tables — one for the `/s:` commands, one for the `shipd`
CLI verbs. Each row SHALL carry the invocation including its argument and
option forms, a one-line description of what the command does, and exactly one
short example invocation. The `/s:` table SHALL carry one row for every
directory under `plugins/s/skills/`, and the `shipd` table SHALL carry one row
for every verb listed in the `shipd --help` banner. Where an option is
accepted by several verbs, the cheatsheet SHALL state it once in a conventions
preamble rather than repeating it on every row. Where a verb requires a
precondition this repository does not meet, its row SHALL name that
precondition rather than omit the verb or invent an invocation that avoids it.

#### Scenario: Every skill has a row
- **WHEN** the `/s:` table's rows are compared against the directory names
  under `plugins/s/skills/`
- **THEN** every directory has exactly one row and no row names a command that
  has no directory

#### Scenario: Every shipd verb has a row
- **WHEN** the `shipd` table's rows are compared against the verb list printed
  by `shipd --help`
- **THEN** every listed verb has exactly one row and no row names a verb the
  banner does not list

#### Scenario: Each row carries one example
- **WHEN** a reader scans any row of either table
- **THEN** that row shows the invocation with its argument and option forms, a
  one-line description, and exactly one example invocation

#### Scenario: Read-only examples run as written
- **WHEN** the read-only examples in the `shipd` table whose rows name no
  precondition are executed verbatim from the repository root
- **THEN** each one runs and exits zero

#### Scenario: A precondition-gated row names its precondition
- **WHEN** a reader scans the row for a verb that cannot succeed here without
  setup — `workspace`, which resolves through the nearest ancestor
  `.shipd-config.json` declaring a `workspace` key
- **THEN** the row names that precondition, and its example is still the
  ordinary invocation rather than one contrived to exit zero

#### Scenario: Shared flags are stated once
- **WHEN** a reader looks for what `--json` or `--root` mean
- **THEN** they are explained in the conventions preamble, and the per-verb
  rows do not repeat that explanation

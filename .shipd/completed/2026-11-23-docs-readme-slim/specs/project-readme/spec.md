## ADDED Requirements

### Requirement: README links each docs group
id: readme-docs-group-links

`README.md` SHALL carry a `## Documentation` section directly after
`## Install`. The section SHALL hold nine list items, in this order, each
opening with the group name in bold and carrying exactly one link into
`docs/`: **Start here** to `docs/getting-started.md`, **Plan** to
`docs/plan.md`, **Build** to `docs/build.md`, **Epics** to `docs/epics.md`,
**Review and merge** to `docs/semantic-review.md`, **Multi-agent PRs** to
`docs/multi-agent-pr.md`, **Knowledge** to `docs/oracle.md`, **Workspaces** to
`docs/workspaces.md`, and **Configure** to `docs/customise.md`. The section
SHALL close with one sentence that links `docs/cheatsheet.md` as the list of
every command.

The level-2 headings of `README.md` SHALL be exactly `## Install`,
`## Documentation`, `## Structure`, `## Adding a command`,
`## Adding a skill`, and `## After editing`, in that order. The file SHALL
total 150 lines or fewer and SHALL hold no table.

#### Scenario: Each group line links its page
- **WHEN** the list items of the README's `## Documentation` section are read
- **THEN** there are nine, their bold names are the nine groups in the order
  this requirement gives, each holds exactly one `docs/` link to the page
  this requirement assigns, and every linked file exists

#### Scenario: The moved sections are gone
- **WHEN** the level-2 headings of `README.md` are listed
- **THEN** they are `## Install`, `## Documentation`, `## Structure`,
  `## Adding a command`, `## Adding a skill`, and `## After editing`, and no
  line of the file starts a table row with `|`

#### Scenario: README fits its cap
- **WHEN** `wc -l README.md` runs
- **THEN** the count is 150 or fewer

## MODIFIED Requirements

### Requirement: README retains onboarding content
id: readme-retains-onboarding-content
base: 980f7ae6d288

The `README.md` SHALL keep the practical guidance no docs page owns: what
the project is, how to install it as a marketplace plugin, the directory
structure, and how to add new commands and skills. It SHALL be ordered
newcomer-first: installation and the links into `docs/` come before the
contributor sections.

#### Scenario: Install instructions survive the rewrite
- **WHEN** a reader wants to try the plugin
- **THEN** the README still shows how to add the marketplace and install
  the `s` plugin, and how to add a new command or skill

#### Scenario: Newcomer content precedes internals
- **WHEN** a reader scans the README top to bottom
- **THEN** `## Install` and `## Documentation`, with its
  `docs/getting-started.md` link, appear before `## Structure`

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs
base: 73d6bb147c40
Dropped: Root README names the options layer

`docs/getting-started.md`'s doctor step SHALL give the `shipd doctor`
command, SHALL link `doctor.md` as the owner of the check list, SHALL NOT
list the check names itself, and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset. The root `README.md` SHALL NOT describe the
autonomous pipeline; the content directory's `README.md` holds its grammar,
as `shipd-config`'s `pipeline-grammar-docs` requirement states.

#### Scenario: Doctor step defers to the doctor page
- **WHEN** a reader reaches the doctor step of `docs/getting-started.md`
- **THEN** it shows `shipd doctor`, links `doctor.md`, and holds no list
  of check names

#### Scenario: Guide mentions the eco opt-in
- **WHEN** a reader searches `docs/getting-started.md` for the
  cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in

#### Scenario: Root README holds no pipeline prose
- **WHEN** `README.md` is searched for `autonomous-pipeline`
- **THEN** no line matches

### Requirement: Harness mode documentation
id: harness-mode-docs
base: 0df33e2bf434
Dropped: Install finish is documented
Dropped: The closing preflight is documented
Dropped: Repo-level installation is documented
Dropped: Feature scaling is explained
Dropped: CLI list gains the harness verb
Dropped: Brand note is stated

`README.md` SHALL NOT document harness mode. Its `## Install` section SHALL
name harness selection in one sentence at most and link `docs/install.md`.
`docs/install.md` SHALL carry the install finish for docs readers: harness
selection, headless degradation, and a link to `harnesses.md` for repo-level
`shipd harness add`; `docs/getting-started.md` SHALL NOT restate it.
`docs/harnesses.md` owns repo-level harness mode, as `harness-registry`'s
`harness-user-docs` requirement states it.

#### Scenario: Install page carries the mode
- **WHEN** a reader follows `docs/install.md`'s harness step
- **THEN** harness selection and headless degradation are named, and
  `harnesses.md` is linked for repo-level `shipd harness add`

#### Scenario: README defers harness mode
- **WHEN** `README.md` is searched for `shipd harness` and `harnesses.json`
- **THEN** no line matches, and its `## Install` section links
  `docs/install.md`

### Requirement: Multi-agent PR entry links
id: multi-agent-pr-entry-links
base: a051efa446b6

The three entry surfaces SHALL link the Multi-agent PR concept doc. The
**Multi-agent PRs** item of `README.md`'s `## Documentation` section SHALL
link `docs/multi-agent-pr.md`. `docs/what-is-shipd.md` SHALL link
`multi-agent-pr.md` in a prose paragraph placed after its Mermaid diagram
and before the paragraph that opens "Today shipd builds itself", and SHALL
stay at 100 lines or fewer. The `/s:room` row of `docs/cheatsheet.md`'s
command table SHALL link `multi-agent-pr.md` in its description cell.

#### Scenario: README links the concept doc
- **WHEN** a reader opens the `## Documentation` section of `README.md`
- **THEN** its **Multi-agent PRs** item contains a link to
  `docs/multi-agent-pr.md`

#### Scenario: Overview links the concept doc within its cap
- **WHEN** `docs_lint.py docs/what-is-shipd.md` runs and `wc -l` counts
  the file
- **THEN** the lint exits `0`, the count is 100 or fewer, and the text
  between the closing Mermaid fence and "Today shipd builds itself"
  contains a link to `multi-agent-pr.md`

#### Scenario: Cheatsheet row links the concept doc
- **WHEN** `docs_lint.py docs/cheatsheet.md` runs and the `/s:room` row of
  its command table is read
- **THEN** the lint exits `0` and the row contains a link to
  `multi-agent-pr.md`

### Requirement: Command cheatsheet
id: cheatsheet-doc
base: f4119d8ac7c1

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
sets are named `Pipeline`, `Orchestration` and `Memory`, in that order. This
requirement owns those three names; `README.md` carries no skill list to take
them from. Each of the fence's seven regions SHALL hold exactly
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

## REMOVED Requirements

### Requirement: README catalogs the plugin's skills
id: readme-catalogs-the-plugin-s-skills
base: eb7d61754b21
Reason: The `docs-by-feature` epic makes `docs/cheatsheet.md` the only list of every skill; the README links it instead of repeating it.
Migration: `cheatsheet-doc` keeps one row per skill and now owns the three group names; each skill's detail lives on its main docs page.

### Requirement: README documents the spec engine and status pipeline
id: readme-documents-spec-engine
base: 1e2d8ca3e1a9
Reason: Docs pages own each of these facts, and the README links the docs groups instead of restating them.
Migration: The layout and terms live on `docs/core-ideas.md`, the lifecycle and guarded transitions on `docs/plan.md`, configuration on `docs/customise.md`, and the statusline and build telemetry on `docs/statusline-and-telemetry.md`.

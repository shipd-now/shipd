## ADDED Requirements

### Requirement: Entry docs conform to the standard
id: entry-docs-standard

The entry path SHALL read `docs/what-is-shipd.md` (concept) →
`docs/getting-started.md` (how-to) → `docs/cheatsheet.md` (reference).
`docs/what-is-shipd.md` SHALL open with a `<!-- doc-type: concept -->`
comment on its first line, SHALL total 100 lines or fewer, SHALL pass
`docs_lint.py`, and SHALL link `getting-started.md` from its prose before
the overview diagram. `docs/quickstart.md` SHALL NOT exist, and no file
under `docs/` outside `docs/retros/`, and no line of `README.md`, SHALL
reference `quickstart.md`.

#### Scenario: What-is doc passes the lint
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/what-is-shipd.md` runs
- **THEN** it exits 0, the first line is the concept marker, and the file is
  at most 100 lines

#### Scenario: What-is doc links the entry how-to
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** a relative link to `getting-started.md` appears before the
  mermaid fence

#### Scenario: Quickstart is gone and unreferenced
- **WHEN** the tree is searched for `quickstart`
- **THEN** `docs/quickstart.md` does not exist, and no match remains under
  `docs/` (outside `docs/retros/`) or in `README.md`

## MODIFIED Requirements

### Requirement: Getting-started guide
id: getting-started-doc
base: 59e8752ebb29

`docs/getting-started.md` SHALL be the single entry how-to: it SHALL open
with a `<!-- doc-type: how-to -->` comment on its first line, total 150
lines or fewer, pass `docs_lint.py`, and walk a newcomer in this order:
install (the one-command installer), the `shipd doctor` preflight, the
`/s:onboard` tour, a first `/s:plan` and `/s:build`, then watching the
result with `shipd board`, `shipd status`, and the statusline. The plan step
SHALL name each planning artifact — `plan.md`, the per-capability delta
`spec.md`, and `tasks.md` — with its purpose and SHALL link the content
directory's `README.md` as the grammar authority. The build step SHALL name
the three durable outcomes: the `change/<name>` branch, the merge into
`verified/`, and the archive under `completed/`. The watch step SHALL give
`shipd statusline install` as the registration command and state that the
written entry resolves the newest cached snapshot rather than a
version-pinned path. The guide SHALL link `docs/cheatsheet.md` from its
closing where-to-go-next section.

#### Scenario: Guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/getting-started.md` runs
- **THEN** it exits 0, the first line is the how-to marker, and the file is
  at most 150 lines

#### Scenario: The walk is ordered install-first
- **WHEN** a reader follows `docs/getting-started.md` top to bottom
- **THEN** install, doctor, onboard, plan, build, and watch appear as steps
  in that order, each naming its exact command

#### Scenario: Artifacts are each explained
- **WHEN** the reader reaches the plan step
- **THEN** `plan.md`, the delta `specs/<capability>/spec.md`, and `tasks.md`
  are each named with their purpose, and the content directory's `README.md`
  is linked as the grammar authority

#### Scenario: Build outcomes are named
- **WHEN** the reader reaches the build step
- **THEN** the change branch, the `verified/` merge, and the `completed/`
  archive are all named as the build's durable outcomes

#### Scenario: Statusline registration survives updates
- **WHEN** the reader reaches the watch step
- **THEN** `shipd statusline install` is the given command, and the text
  states the registered entry resolves the newest cached snapshot rather
  than a version-pinned path

#### Scenario: Guide points at the cheatsheet
- **WHEN** a reader reaches the guide's closing where-to-go-next section
- **THEN** a relative link to `cheatsheet.md` is present there

### Requirement: Command cheatsheet
id: cheatsheet-doc
base: e7ec063bffc9

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

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs
base: 1d24d6a80a72

The root `README.md`'s autonomous-pipeline overview SHALL mention that
entries may carry typed per-stage options validated strictly (unknown keys
and wrong types rejected) by the engine's stdlib-only schema module,
requiring no third-party package, linking the format authority for the full
grammar. `docs/getting-started.md`'s doctor step SHALL list the checks the
`shipd doctor` verb reports and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Doctor list matches the shipped checks
- **WHEN** a reader compares the doctor step's check list in
  `docs/getting-started.md` against a `shipd doctor` run
- **THEN** every check the verb reports appears in the list

#### Scenario: Guide mentions the eco opt-in
- **WHEN** a reader searches `docs/getting-started.md` for the
  cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in

### Requirement: Harness mode documentation
id: harness-mode-docs
base: 15b3b9b11bdf

The `README.md` SHALL document the harness mode inside its installation
documentation: the interactive install finish (`shipd install`) — the
animated wordmark, the harness multi-select over the registry's fourteen
harnesses, the selection record at `~/.shipd/harnesses.json`, user-global
command generation for harnesses declaring a user-global directory, the
read-only `shipd doctor` preflight that closes a confirmed finish (and its
absence on the headless and aborted paths), the
headless degradation that prints a note and writes nothing, and re-running
`shipd install` to reopen the selection — and, in an explicitly labeled
harness-mode subsection, the repo-level `shipd harness add`/`remove` actions
(the ownership marker, idempotent refresh, refusal of unmarked files without
`--force`, `--user` for the user-global surfaces, and harnesses without a
surface reported as skipped), the feature-scaling model (the declared feature
vocabulary `subagents`, `question-dialogs`, `file-references`,
`background-tasks`; one shared body per command rendered per harness so a
generated file never mentions a feature its harness did not declare; the
`shipd-` command-id prefix), and `shipd harness` / `shipd harness show <id>`
as the inspection verbs. The README's CLI verb list SHALL include the
`harness` verb. The harness documentation SHALL carry the brand note: the
animated wordmark is confined to the install surface and ☕ remains the
brand mark. `docs/getting-started.md`'s install step SHALL mention the
harness selection step and its headless degradation, and the guide SHALL
name `shipd harness add` as the way to install the generated commands into
a repository.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the interactive `shipd install` finish is described with the
  harness multi-select, the `~/.shipd/harnesses.json` selection record, the
  headless write-nothing degradation, and re-running `shipd install` to
  reopen the selection

#### Scenario: The closing preflight is documented
- **WHEN** a reader finishes the README's install finish paragraph
- **THEN** it states that a confirmed finish closes by running the read-only
  `shipd doctor` preflight, and that the headless and aborted paths do not

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with the ownership
  marker, the idempotent re-run, `--force` for unmarked files, and `--user`
  for the user-global surfaces

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** the four declared features are named and the text states that a
  generated file never mentions a feature its harness did not declare

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with the verb's registry
  list/show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it states the animated wordmark appears only on the install
  surface and that ☕ remains the brand mark

#### Scenario: Getting started carries the mode
- **WHEN** a reader follows `docs/getting-started.md`'s install step
- **THEN** the harness selection step and its headless degradation are
  mentioned, and `shipd harness add` is named for repo-level installs

### Requirement: README retains onboarding content
id: readme-retains-onboarding-content
base: c684b5e5bb5b

The `README.md` SHALL preserve the existing practical guidance: what the
project is, how to install it as a marketplace/plugin, the directory
structure, and how to add new commands and skills, ordered newcomer-first —
installation and the `docs/getting-started.md` link before the engine
internals.

#### Scenario: Install instructions survive the rewrite
- **WHEN** a reader wants to try the plugin
- **THEN** the README still shows how to add the marketplace and install
  the `s` plugin, and how to add a new command or skill

#### Scenario: Newcomer content precedes internals
- **WHEN** a reader scans the README top to bottom
- **THEN** installation and the `docs/getting-started.md` link appear
  before the spec-engine and statusline internals

## REMOVED Requirements

### Requirement: Quickstart document
id: quickstart-doc
base: 723adc6482ff
Reason: The docs-rewrite epic merges the entry walkthroughs — `docs/quickstart.md` is deleted and `docs/getting-started.md` becomes the single entry how-to.
Migration: The quickstart's obligations (install through watch, each step with its exact command) move into the modified `getting-started-doc` requirement; the README's newcomer link retargets under `readme-retains-onboarding-content`.

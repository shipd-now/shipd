## MODIFIED Requirements

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs
base: 0f1eb0e388cf
Dropped: Doctor list matches the shipped checks

The root `README.md`'s autonomous-pipeline overview SHALL mention that
entries may carry typed per-stage options validated strictly (unknown keys
and wrong types rejected) by the engine's stdlib-only schema module,
requiring no third-party package, linking the format authority for the full
grammar. `docs/getting-started.md`'s doctor step SHALL give the `shipd doctor`
command, SHALL link `doctor.md` as the owner of the check list, SHALL NOT
list the check names itself, and SHALL carry a one-line mention that
`{"autonomous-pipeline": "eco"}` in `.shipd-config.json` opts a delivery
into the cheap preset.

#### Scenario: Root README names the options layer
- **WHEN** a reader finishes the README's autonomous-pipeline paragraph
- **THEN** it names typed per-stage options and strict validation and
  points at the format authority for the grammar

#### Scenario: Doctor step defers to the doctor page
- **WHEN** a reader reaches the doctor step of `docs/getting-started.md`
- **THEN** it shows `shipd doctor`, links `doctor.md`, and holds no list
  of check names

#### Scenario: Guide mentions the eco opt-in
- **WHEN** a reader searches `docs/getting-started.md` for the
  cheap-delivery opt-in
- **THEN** one line shows `{"autonomous-pipeline": "eco"}` as the way to
  opt in

### Requirement: Harness mode documentation
id: harness-mode-docs
base: ecc8f8987338
Dropped: Getting started carries the mode

The `README.md` SHALL document harness mode inside its installation documentation: the interactive `shipd install` finish, animated wordmark, harness multi-select over the registry's fifteen harnesses, `~/.shipd/harnesses.json` selection record, user-global generation, closing setup check that shows one progress line, installs missing local tooling, and lists only the remaining problems with a fix each, headless degradation, and re-run path. Its explicitly labeled harness-mode subsection SHALL cover repo-level `shipd harness add` and `remove`, ownership and overwrite safety, `--user`, skipped unsupported surfaces, the four-feature scaling model, `shipd-` command names, and registry inspection verbs. The CLI verb list SHALL include `harness`; the brand note SHALL remain present. `docs/install.md` SHALL carry the install finish for docs readers: harness selection, headless degradation, and a link to `harnesses.md` for repo-level `shipd harness add`; `docs/getting-started.md` SHALL NOT restate it.

#### Scenario: Install finish is documented
- **WHEN** a reader finishes the README's install-mode documentation
- **THEN** the fifteen-harness multi-select, selection record, headless write-nothing degradation, and re-run path are described

#### Scenario: The closing preflight is documented
- **WHEN** a reader finishes the README's install finish paragraph
- **THEN** it states that a confirmed finish runs the setup check, installs missing local tooling, lists each remaining problem with its fix, and that headless and aborted paths do not

#### Scenario: Repo-level installation is documented
- **WHEN** a reader reaches the README's harness-mode subsection
- **THEN** `shipd harness add` and `remove` appear with ownership, idempotence, `--force`, and `--user` behavior

#### Scenario: Feature scaling is explained
- **WHEN** a reader reaches the feature-scaling explanation
- **THEN** all four declared features are named and generated files are described as omitting undeclared features

#### Scenario: CLI list gains the harness verb
- **WHEN** a reader reads the README's CLI verb list
- **THEN** it includes a `harness` row consistent with registry list and show behavior

#### Scenario: Brand note is stated
- **WHEN** a reader reaches the harness documentation's brand note
- **THEN** it confines the animated wordmark to installation and retains ☕ as the brand mark

#### Scenario: Install page carries the mode
- **WHEN** a reader follows `docs/install.md`'s harness step
- **THEN** harness selection and headless degradation are named, and `harnesses.md` is linked for repo-level `shipd harness add`

### Requirement: Entry docs conform to the standard
id: entry-docs-standard
base: 5d4db84ecc08

The entry path SHALL read `docs/what-is-shipd.md` (concept) →
`docs/install.md` (how-to) → `docs/getting-started.md` (how-to) →
`docs/core-ideas.md` (concept) → `docs/cheatsheet.md` (reference).
`docs/what-is-shipd.md` SHALL open with a `<!-- doc-type: concept -->`
comment on its first line, SHALL total 100 lines or fewer, SHALL pass
`docs_lint.py`, and SHALL link `getting-started.md` from its prose before
the overview diagram, labelling that link "Your first change". Its prose
SHALL also link `core-ideas.md`, and the overview diagram's review stage
SHALL be a subgraph titled `Review and merge`, the name of the docs group
that documents it. `docs/quickstart.md` SHALL NOT exist, and no file
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

#### Scenario: What-is doc matches the regrouped docs
- **WHEN** `docs/what-is-shipd.md` is read top to bottom
- **THEN** the `getting-started.md` link is labelled "Your first change", a
  relative link to `core-ideas.md` is present, and the mermaid fence holds
  a subgraph titled `Review and merge` and none titled `Ship`

## ADDED Requirements

### Requirement: Core ideas page
id: core-ideas-doc

The repository SHALL provide `docs/core-ideas.md`, titled "Core ideas", with
`<!-- doc-type: concept -->` as its first line, 100 lines or fewer, passing
`docs_lint.py`. The page SHALL define each shipd term once, in three
sentences or fewer, and link the page that owns the detail. Its level-2
sections SHALL be, in order: `## The spec`, `## A change`, `## Gates`,
`## Agents`, `## Epics`, `## Knowledge`, and `## Workspaces`. They SHALL
define and link:

- the capability library under `verified/` and a requirement with its
  scenarios, linking the content directory's `README.md`;
- a change, its three artifacts, the delta, and the statuses `draft`,
  `ready`, `active`, `complete`, `verified`, and `rejected`, linking
  `plan.md`; and the one change, one worktree, one branch, one pull request
  rule, linking `worktrees.md` and `pr.md`;
- the context gate (`plan.md`), the supersession gate
  (`supersession-gate.md`), the semantic review (`semantic-review.md`), and
  the review gate (`copilot-review.md`);
- the orchestrator, the execution agents one model tier down, and the
  validator (`build.md`); and the room (`multi-agent-pr.md`);
- an epic and its members (`epics.md`), autopilot (`autopilot.md`), and the
  initiative and PRD above an epic (`prd.md`);
- the memory, oracle, human ladder (`oracle.md`), the wiki (`wiki.md`), and
  personal memory (`memory.md`);
- a workspace (`workspaces.md`) and the layered configuration
  (`customise.md`).

The page SHALL link `what-is-shipd.md` as the owner of the overview diagram
and `cheatsheet.md` as the command list. It SHALL carry no mermaid fence, no
table, and no shell command. It SHALL NOT take the feature main-page shape.

#### Scenario: Page passes the lint within its cap
- **WHEN** `docs_lint.py docs/core-ideas.md` runs
- **THEN** it exits 0, the first line is the concept marker, and the file is
  at most 100 lines

#### Scenario: Every idea links its owner
- **WHEN** the relative links of `docs/core-ideas.md` are collected
- **THEN** they include each of the eighteen docs pages this requirement
  names and the content directory's `README.md`, and every link resolves

#### Scenario: Page stays a concept page
- **WHEN** `docs/core-ideas.md` is read
- **THEN** its level-2 headings are the seven this requirement names, in
  order, and it holds no mermaid fence, no table row, and no code fence

### Requirement: First-change guide defers to the owner pages
id: first-change-guide-owners

`docs/getting-started.md` SHALL be titled `# Your first change` and SHALL be
the main page for `/s:onboard`. It SHALL keep its six numbered step headings
and its closing `## Where to go next` heading unchanged, so the anchor
`#1-install` still resolves, and SHALL NOT take the feature main-page shape.
Each step SHALL state a fact another page owns in one sentence at most and
link that page: `install.md` from the install step, `doctor.md` from the
doctor step, `plan.md` from the plan step, `build.md` from the build step,
and `statusline-and-telemetry.md` from the watch step. The closing section
SHALL link `cheatsheet.md`, `core-ideas.md`, `what-is-shipd.md`, and
`workspaces.md`.

#### Scenario: Guide is retitled and keeps its anchors
- **WHEN** the headings of `docs/getting-started.md` are listed
- **THEN** the level-1 heading is `# Your first change`, and the level-2
  headings begin `## 1. Install` and end `## Where to go next`

#### Scenario: Each step links its owner
- **WHEN** the relative links of `docs/getting-started.md` are collected
- **THEN** they include `install.md`, `doctor.md`, `plan.md`, `build.md`,
  `statusline-and-telemetry.md`, `customise.md`, `cheatsheet.md`,
  `core-ideas.md`, `what-is-shipd.md`, and `workspaces.md`, and each resolves

### Requirement: Cheatsheet rows link each command's main page
id: cheatsheet-page-links

In both tables of `docs/cheatsheet.md`, each row's description cell SHALL
carry exactly one relative link, to the command's main page:

- `/s:` rows: `ask` to `oracle.md`; `autopilot` to `autopilot.md`; `build`
  to `build.md`; `demo` and `drive` to `drive-and-demo.md`; `doctor` to
  `doctor.md`; `document` to `document.md`; `drift` to `drift.md`; `duck` to
  `duck.md`; `epic` and
  `explain` to `epics.md`; `epic-grill` to `epic-grill.md`; `fix` to
  `fix.md`; `forget`, `memory`, and `remember` to `memory.md`; `gate` to
  `copilot-review.md`; `init` to `customise.md`; `initiative` to
  `initiatives.md`; `onboard` to `getting-started.md`; `plan`, `plan-deep`,
  and `status` to `plan.md`; `pr` to `pr.md`; `prd` to `prd.md`; `research`
  to `research.md`; `review` to `semantic-review.md`; `room` to
  `multi-agent-pr.md`; `teach` to `wiki.md`; `video-ingest` to
  `video-ingest.md`; `workspace` to `workspaces.md`; `worktree-hooks` to
  `worktrees.md`.
- `shipd` rows: `init` and `config` to `customise.md`; `list`, `status`,
  `locate`, and `lint` to `plan.md`; `related` to `fix.md`; `search` and
  `render` to `prd-reference.md`; `epic` to `epics.md`; `prd` to `prd.md`;
  `workspace` to `workspaces.md`; `wiki` to `wiki.md`; `board` to
  `build.md`; `metrics` and `statusline` to `statusline-and-telemetry.md`;
  `worktree` to `worktrees.md`; `room` to `room-run.md`; `doctor` to
  `doctor.md`; `copilot` to `copilot-review.md`; `gate` to `pr.md`;
  `harness` to `harnesses.md`; `vendor`, `install`, and `update` to
  `install.md`.

The `/s:document` row SHALL link `document.md`. The file's level-2 headings SHALL be exactly `## Conventions`,
`## How the skills overlap`, `## /s: commands`, and `## shipd CLI`; the
`doctor --fix` detail lives on `doctor.md`. The intro SHALL label its
`getting-started.md` link "Your first change".

#### Scenario: Every row links one existing page
- **WHEN** the relative links in each table row of `docs/cheatsheet.md` are
  collected
- **THEN** every row holds exactly one, it names the page
  this requirement assigns, and the file exists

#### Scenario: The cheatsheet holds lists only
- **WHEN** the level-2 headings of `docs/cheatsheet.md` are listed
- **THEN** they are `## Conventions`, `## How the skills overlap`,
  `## /s: commands`, and `## shipd CLI`, and no heading names `doctor --fix`

#### Scenario: The drifted rows are present
- **WHEN** the tables are compared against `plugins/s/skills/` and the
  `shipd --help` banner
- **THEN** a `/s:demo` row, a `room` row, and a `gate rules` row exist, and
  `s:demo` appears once in the list beneath the venn fence

### Requirement: Feature pages link across groups
id: feature-page-cross-links

Each feature main page under `docs/` SHALL link the first mention of a
`/s:` skill or a `shipd` verb that another page owns to that owner page.
The owner of each command SHALL be the page the `cheatsheet-page-links`
requirement assigns it. The sweep SHALL cover every main page the eight
feature groups wrote or reshaped, and `docs/document.md`. A link SHALL sit
in prose or in a table cell, never in a heading or inside a code fence. A
page SHALL link a given owner page at most once through this sweep, and
SHALL NOT link itself. The sweep SHALL reword nothing beyond adding the
link, and every swept page SHALL stay within its line cap and pass
`docs_lint.py`.

#### Scenario: A foreign skill's first mention is a link
- **WHEN** `docs/build.md` is inspected
- **THEN** its first prose mention of `/s:plan` links `plan.md`

#### Scenario: Swept pages stay within their caps
- **WHEN** `docs_lint.py` runs over every swept page
- **THEN** it exits 0 and no page exceeds the cap of its doc type

#### Scenario: Every added link resolves
- **WHEN** the relative links on the swept pages are collected
- **THEN** each names an existing file under `docs/`


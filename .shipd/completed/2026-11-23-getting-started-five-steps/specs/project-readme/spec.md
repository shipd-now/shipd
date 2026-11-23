## MODIFIED Requirements

### Requirement: Pipeline follower surfaces stay current
id: pipeline-follower-docs
base: 188efda95746
Dropped: Doctor step defers to the doctor page
Dropped: Guide mentions the eco opt-in

`docs/getting-started.md` SHALL carry no doctor step and SHALL name neither
`shipd doctor` nor the `autonomous-pipeline` key. `docs/doctor.md` owns the
preflight, and `docs/customise.md` owns the presets, the `eco` preset among
them. The root `README.md` SHALL NOT describe the autonomous pipeline; the
content directory's `README.md` holds its grammar, as `shipd-config`'s
`pipeline-grammar-docs` requirement states.

#### Scenario: Guide holds no doctor step
- **WHEN** `docs/getting-started.md` is searched for `shipd doctor` and
  `doctor.md`
- **THEN** no line matches

#### Scenario: Guide leaves the eco opt-in to its owner
- **WHEN** `docs/getting-started.md` is searched for `autonomous-pipeline`
- **THEN** no line matches, and `docs/customise.md` still names the `eco`
  preset

#### Scenario: Root README holds no pipeline prose
- **WHEN** `README.md` is searched for `autonomous-pipeline`
- **THEN** no line matches

### Requirement: Getting-started guide
id: getting-started-doc
base: 9c84cede3f35
Dropped: The walk is ordered install-first

`docs/getting-started.md` SHALL be the single entry how-to: it SHALL open
with a `<!-- doc-type: how-to -->` comment on its first line, total 150
lines or fewer, pass `docs_lint.py`, and walk a newcomer through five steps
in this order: install, a first `/s:plan`, `/s:build`, the statusline, then
the board. A short opening SHALL precede the steps: it SHALL hold no list
or table of the commands, and no overview box.

The install step SHALL show only the one-command installer in a code fence,
followed by one collapsed block: an HTML `<details>` element whose
`<summary>` reads `Alternative install`. The block SHALL name the other
install modes in three sentences or fewer and link `install.md`, which owns
them. The step SHALL show no installer output and SHALL name no setup
check.

The plan step SHALL name each planning artifact — `plan.md`, the
per-capability delta `spec.md`, and `tasks.md` — with its purpose and SHALL
link the content directory's `README.md` as the grammar authority. The
build step SHALL name the three durable outcomes: the `change/<change>`
branch, the merge into `verified/`, and the archive under `completed/`.

The statusline step SHALL follow the build step and precede the board step.
It SHALL give `shipd statusline install` as the registration command, SHALL
state that the command writes the `statusLine` entry into
`~/.claude/settings.json`, and SHALL state that the entry resolves the
newest installed shipd at each render, so it survives an update. It SHALL
state that the statusline works in Claude Code only and that no other
harness has a statusline integration.

The board step SHALL give `shipd board` in a code fence and SHALL name
`shipd status` and `shipd list` in one sentence at most. The guide SHALL
link `docs/cheatsheet.md` from its closing where-to-go-next section.

#### Scenario: Guide passes the lint within its cap
- **WHEN** `python3 plugins/s/skills/document/scripts/docs_lint.py
  docs/getting-started.md` runs
- **THEN** it exits 0, the first line is the how-to marker, and the file is
  at most 150 lines

#### Scenario: The walk is five steps, install first
- **WHEN** a reader follows `docs/getting-started.md` top to bottom
- **THEN** install, plan, build, statusline, and board appear as five
  numbered steps in that order, each naming its exact command

#### Scenario: The opening holds no command overview
- **WHEN** the text between the title and `## 1. Install` is read
- **THEN** it holds no list item, no table row, and no code fence

#### Scenario: Install shows one command and one collapsed block
- **WHEN** the install step is read
- **THEN** it holds one code fence with `curl -fsSL https://shipd.now/install
  | sh`, then a `<details>` block with the summary `Alternative install` that
  links `install.md`, and no other prose

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
- **WHEN** the reader reaches the statusline step
- **THEN** `shipd statusline install` is the given command, and the text
  states the registered entry resolves the newest installed shipd at each
  render

#### Scenario: Statusline is scoped to Claude Code
- **WHEN** the reader reaches the statusline step
- **THEN** it names `~/.claude/settings.json`, and it states that the
  statusline works in Claude Code only

#### Scenario: Board step stays short
- **WHEN** the reader reaches the board step
- **THEN** `shipd board` is the one command in a code fence, and one
  sentence names `shipd status` and `shipd list`

#### Scenario: Guide points at the cheatsheet
- **WHEN** a reader reaches the guide's closing where-to-go-next section
- **THEN** a relative link to `cheatsheet.md` is present there

### Requirement: First-change guide defers to the owner pages
id: first-change-guide-owners
base: f925844b6fb6
Dropped: Guide is retitled and keeps its anchors

`docs/getting-started.md` SHALL be titled `# Your first change`. Its
level-2 headings SHALL be exactly `## 1. Install`,
`## 2. Plan your first change`, `## 3. Build it`,
`## 4. Turn on the statusline`, `## 5. Watch the board`, and
`## Where to go next`, in that order, so the anchor `#1-install` still
resolves. It SHALL NOT take the feature main-page shape. It SHALL NOT be
the main page for `/s:onboard` and SHALL NOT name `/s:onboard`: `onboard.md`
owns the tour, as `shipd-onboard`'s `onboard-user-docs` requirement states.

Each step SHALL state a fact another page owns in one sentence at most and
link that page: `install.md` from the install step, `plan.md` from the plan
step, `build.md` from the build step, and `statusline-and-telemetry.md`
from the statusline step. The closing section SHALL link `cheatsheet.md`,
`what-is-shipd.md`, `core-ideas.md`, `customise.md`, and `workspaces.md`.

#### Scenario: Guide keeps its title and its install anchor
- **WHEN** the headings of `docs/getting-started.md` are listed
- **THEN** the level-1 heading is `# Your first change`, and the level-2
  headings are the six this requirement names, in order

#### Scenario: Each step links its owner
- **WHEN** the relative links of `docs/getting-started.md` are collected
- **THEN** they include `install.md`, `plan.md`, `build.md`,
  `statusline-and-telemetry.md`, `customise.md`, `cheatsheet.md`,
  `core-ideas.md`, `what-is-shipd.md`, and `workspaces.md`, and each resolves

#### Scenario: The tour has left the guide
- **WHEN** `docs/getting-started.md` is searched for `onboard`
- **THEN** no line matches

#### Scenario: The linked anchor still resolves
- **WHEN** the link `getting-started.md#1-install` in
  `docs/copilot-review.md` is followed
- **THEN** it lands on the heading `## 1. Install`

### Requirement: Cheatsheet rows link each command's main page
id: cheatsheet-page-links
base: 99aef8855bd5

In both tables of `docs/cheatsheet.md`, each row's description cell SHALL
carry exactly one relative link, to the command's main page:

- `/s:` rows: `ask` to `oracle.md`; `autopilot` to `autopilot.md`; `build`
  to `build.md`; `demo` and `drive` to `drive-and-demo.md`; `doctor` to
  `doctor.md`; `document` to `document.md`; `drift` to `drift.md`; `duck` to
  `duck.md`; `epic` and
  `explain` to `epics.md`; `epic-grill` to `epic-grill.md`; `fix` to
  `fix.md`; `forget`, `memory`, and `remember` to `memory.md`; `gate` to
  `copilot-review.md`; `init` to `customise.md`; `initiative` to
  `initiatives.md`; `onboard` to `onboard.md`; `plan`, `plan-deep`,
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

#### Scenario: The tour row links the tour page
- **WHEN** the `/s:onboard` row of `docs/cheatsheet.md` is read
- **THEN** its one relative link names `onboard.md` with the link text
  `Guided tour`, and it holds no link to `getting-started.md`

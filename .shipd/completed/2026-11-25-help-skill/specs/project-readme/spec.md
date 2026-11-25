## MODIFIED Requirements

### Requirement: Cheatsheet rows link each command's main page
id: cheatsheet-page-links
base: 68aad211b7e0

In both tables of `docs/cheatsheet.md`, each row's description cell SHALL
carry exactly one relative link, to the command's main page:

- `/s:` rows: `ask` to `oracle.md`; `autopilot` to `autopilot.md`; `build`
  to `build.md`; `demo` and `drive` to `drive-and-demo.md`; `doctor` to
  `doctor.md`; `document` to `document.md`; `drift` to `drift.md`; `duck` to
  `duck.md`; `epic` and
  `explain` to `epics.md`; `epic-grill` to `epic-grill.md`; `fix` to
  `fix.md`; `forget`, `memory`, and `remember` to `memory.md`; `gate` to
  `copilot-review.md`; `help` to `help.md`; `init` to `customise.md`; `initiative` to
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

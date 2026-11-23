# shipd-initiative

### Requirement: Initiative workflow skill
id: initiative-workflow-skill

An `/s:initiative` skill SHALL provide, selected by argument: `new <slug>`
— a workspace-first interview (existing briefs and declared project slugs
read via the engine's show and `cat` verbs before asking; one batched
question round for the goal, outcome requirements, and optional `Project:`
scope) that authors the brief in a staging area and installs it at
`Status: open` through `spec_emit.py initiative <slug> --from <file>` (no
PR — briefs live outside the repo, and the skill SHALL NOT construct the
brief's path or write it directly); `list` — every initiative's status,
requirement progress, and project scope via the status CLI; and
`review <slug>` — walking the brief's requirements with the user, ticking
outcomes the user confirms achieved, then running `initiative-sync`. When
no workspace root is discoverable, every verb SHALL stop with the CLI's
no-workspace error rather than inventing a location, and SHALL point the
user at `/s:workspace init` as the setup path.

#### Scenario: New emits a lint-clean open brief through the engine
- **WHEN** the skill's `new` verb completes for `mvp-readiness`
- **THEN** the brief was installed via `spec_emit.py initiative`, exists
  with `Status: open` and outcome checkboxes at the workspace's resolved
  brief path, and `--initiative mvp-readiness` exits zero

#### Scenario: No workspace stops the skill and names the remedy
- **WHEN** any verb runs where no workspace root is discoverable
- **THEN** the skill reports the no-workspace error, writes nothing, and
  points the user at `/s:workspace init`

### Requirement: Initiative attachment to epics
id: initiative-attachment

The skill's `set <epic> <initiative>` verb SHALL tag an epic with exactly
one initiative by driving the status CLI's `epic-set-initiative` verb —
never editing the epic file by hand — and SHALL ship the edit through the
repository's worktree-and-PR workflow (never a direct commit to main),
verifying with the linter's `--epic` mode that the epic and the initiative
reference are valid before shipping. Asked to attach an initiative to a
change that carries `Epic:`, the skill SHALL refuse and point at the epic
as the attachment point.

#### Scenario: Set tags the epic through the engine and ships a PR
- **WHEN** `set workspace-projects mvp-readiness` completes
- **THEN** `epic-set-initiative` wrote the single `Initiative:` header
  line, the edit arrives on main via an auto-merging PR, and
  `--epic workspace-projects` exits zero

#### Scenario: Change with an epic is refused
- **WHEN** the user asks to attach an initiative to a change whose plan
  carries `Epic:`
- **THEN** the skill refuses and names the epic to tag instead

### Requirement: Initiatives user documentation
id: initiatives-user-docs

The repository SHALL provide `docs/initiatives.md`, the main page for
`/s:initiative`, titled "Initiatives". The page SHALL conform to the shipd
documentation standard with `<!-- doc-type: how-to -->` as its first line,
and SHALL open by saying what an initiative is, then hold exactly three level-2
sections in this order: `## When to use it`, `## How to run it`, and
`## Reference`.

The page SHALL state:

- that an initiative is a workspace brief stating the outcomes an epic
  delivers against, and that it sits above epics;
- that a brief lives in the workspace, at `initiatives/<slug>/brief.md`
  under the workspace's content directory, and that every verb needs a
  discoverable workspace;
- the shape of a brief in one example fence: the title, `Status: open`, the
  optional `Project:` line, a goal sentence, and a `## Requirements` list of
  checkbox outcomes;
- that a requirement is an outcome, never a task;
- the three statuses `open`, `achieved`, and `dropped`, and that `achieved`
  is derived once every requirement is ticked;
- the run as numbered steps: create a brief with `/s:initiative new <slug>`,
  attach it with `/s:initiative set <epic> <initiative>`, and tick outcomes
  with `/s:initiative review <slug>`;
- that `new` and `review` write only to the workspace and open no pull
  request, while `set` edits the epic's header and ships as a pull request;
- that an epic carries exactly one initiative, that a member derives its
  initiative through its epic, and that `set` refuses a member change;
- that a standalone change carries its own `Initiative:` line.

The `## Reference` section SHALL hold one table of the four verbs `new`,
`list`, `review`, and `set`, each with its arguments and what it writes,
and SHALL name `shipd workspace` as the roster view and
`shipd lint --initiative <slug>` as the check. The page SHALL link
`epics.md`, `workspaces.md`, and `prd.md` as the owner of the hierarchy
diagram, and SHALL carry no mermaid fence. Every command on the page SHALL
be a `/s:` skill or a `shipd` verb.

#### Scenario: Page covers where a brief lives
- **WHEN** `docs/initiatives.md` is inspected
- **THEN** it states that a brief lives in the workspace, shows the brief
  shape with `Status: open` and checkbox requirements, and names the three
  statuses

#### Scenario: Page covers the attachment rules
- **WHEN** `docs/initiatives.md` is inspected
- **THEN** it states that an epic carries one initiative, that `set` ships
  as a pull request, and that `set` refuses a member change

#### Scenario: Reference table lists the four verbs
- **WHEN** the `## Reference` section is read
- **THEN** its table holds `new`, `list`, `review`, and `set`, and the
  section names `shipd workspace` and `shipd lint --initiative <slug>`

#### Scenario: Page passes the lint and its links resolve
- **WHEN** `docs_lint.py` runs over `docs/initiatives.md`
- **THEN** it exits 0 with the file marked `how-to`, the file holds no
  mermaid fence and no engine script path, and every relative link resolves
